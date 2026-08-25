from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from orion.integrations._mcp.langchain import create_mcp_tools


# ==========================================================
# Helpers
# ==========================================================


def make_tool_schema(
    name: str,
    description: str = "",
    parameters: dict | None = None,
) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters
            or {
                "type": "object",
                "properties": {},
            },
        },
    }


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def session_id():
    return uuid4()


@pytest.fixture
def correlation_id():
    return uuid4()


# ==========================================================
# Empty Manager
# ==========================================================


def test_create_mcp_tools_empty(
    session_id,
    correlation_id,
) -> None:
    manager = AsyncMock()
    manager.tools = []

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    assert tools == []


# ==========================================================
# Tool Conversion
# ==========================================================


def test_create_mcp_tools(
    session_id,
    correlation_id,
) -> None:
    manager = AsyncMock()

    manager.tools = [
        make_tool_schema(
            name="read_file",
            description="Read a file.",
        )
    ]

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    assert len(tools) == 1

    tool = tools[0]

    assert tool.name == "read_file"
    assert tool.description == "Read a file."


def test_create_multiple_mcp_tools(
    session_id,
    correlation_id,
) -> None:
    manager = AsyncMock()

    manager.tools = [
        make_tool_schema(
            name="read_file",
            description="Read a file.",
        ),
        make_tool_schema(
            name="write_file",
            description="Write a file.",
        ),
        make_tool_schema(
            name="list_directory",
            description="List a directory.",
        ),
    ]

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    assert len(tools) == 3

    assert [tool.name for tool in tools] == [
        "read_file",
        "write_file",
        "list_directory",
    ]


# ==========================================================
# Schema
# ==========================================================


def test_create_mcp_tool_preserves_schema(
    session_id,
    correlation_id,
) -> None:
    manager = AsyncMock()

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file.",
            },
        },
        "required": ["path"],
    }

    manager.tools = [
        make_tool_schema(
            name="read_file",
            description="Read a file.",
            parameters=parameters,
        )
    ]

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    tool = tools[0]

    assert tool.args == parameters


def test_create_mcp_tool_uses_default_schema(
    session_id,
    correlation_id,
) -> None:
    manager = AsyncMock()

    manager.tools = [
        {
            "type": "function",
            "function": {
                "name": "ping",
                "description": "Ping the server.",
            },
        }
    ]

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    tool = tools[0]

    assert tool.args == {
        "properties": {},
        "type": "object",
    }


# ==========================================================
# Tool Execution
# ==========================================================


@pytest.mark.asyncio
async def test_mcp_tool_calls_manager(
    session_id,
    correlation_id,
) -> None:
    manager = AsyncMock()

    manager.tools = [
        make_tool_schema(
            name="read_file",
            description="Read a file.",
        )
    ]

    manager.call_tool.return_value = "file contents"

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    result = await tools[0].ainvoke(
        {
            "path": "/tmp/test.txt",
        }
    )

    assert result == "file contents"

    manager.call_tool.assert_awaited_once_with(
        "read_file",
        {
            "path": "/tmp/test.txt",
        },
        session_id=session_id,
        correlation_id=correlation_id,
    )


@pytest.mark.asyncio
async def test_mcp_tools_call_correct_tool(
    session_id,
    correlation_id,
) -> None:
    """
    Ensure every generated tool captures its own MCP tool name.
    """

    manager = AsyncMock()

    manager.tools = [
        make_tool_schema("read_file"),
        make_tool_schema("write_file"),
        make_tool_schema("list_directory"),
    ]

    manager.call_tool.side_effect = [
        "read result",
        "write result",
        "list result",
    ]

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    assert await tools[0].ainvoke({"path": "a"}) == "read result"
    assert await tools[1].ainvoke({"path": "b"}) == "write result"
    assert await tools[2].ainvoke({"path": "c"}) == "list result"

    assert manager.call_tool.await_args_list[0].args == (
        "read_file",
        {"path": "a"},
    )

    assert manager.call_tool.await_args_list[1].args == (
        "write_file",
        {"path": "b"},
    )

    assert manager.call_tool.await_args_list[2].args == (
        "list_directory",
        {"path": "c"},
    )


# ==========================================================
# Request Context
# ==========================================================


@pytest.mark.asyncio
async def test_mcp_tool_passes_request_context(
    session_id,
    correlation_id,
) -> None:
    manager = AsyncMock()

    manager.tools = [
        make_tool_schema("read_file"),
    ]

    manager.call_tool.return_value = "result"

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    await tools[0].ainvoke(
        {
            "path": "/tmp/test.txt",
        }
    )

    manager.call_tool.assert_awaited_once_with(
        "read_file",
        {
            "path": "/tmp/test.txt",
        },
        session_id=session_id,
        correlation_id=correlation_id,
    )


# ==========================================================
# Error Propagation
# ==========================================================


@pytest.mark.asyncio
async def test_mcp_tool_propagates_manager_failure(
    session_id,
    correlation_id,
) -> None:
    manager = AsyncMock()

    manager.tools = [
        make_tool_schema("read_file"),
    ]

    manager.call_tool.side_effect = RuntimeError(
        "MCP tool execution failed"
    )

    tools = create_mcp_tools(
        manager,
        session_id=session_id,
        correlation_id=correlation_id,
    )

    with pytest.raises(
        RuntimeError,
        match="MCP tool execution failed",
    ):
        await tools[0].ainvoke(
            {
                "path": "/tmp/test.txt",
            }
        )
