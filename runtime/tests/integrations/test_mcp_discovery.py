# runtime/tests/integrations/test_mcp_discovery.py

from __future__ import annotations

from types import SimpleNamespace

from orion.integrations._mcp.discovery import (
    mcp_tools_to_openai,
)


def test_converts_single_tool() -> None:
    tool = SimpleNamespace(
        name="read_file",
        description="Read a file",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                },
            },
            "required": ["path"],
        },
    )

    result = SimpleNamespace(
        tools=[tool],
    )

    schemas = mcp_tools_to_openai(result)

    assert schemas == [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                        },
                    },
                    "required": ["path"],
                },
            },
        }
    ]


def test_converts_multiple_tools() -> None:
    result = SimpleNamespace(
        tools=[
            SimpleNamespace(
                name="read_file",
                description="Read a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                        }
                    },
                },
            ),
            SimpleNamespace(
                name="list_directory",
                description="List directory contents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                        }
                    },
                },
            ),
        ]
    )

    schemas = mcp_tools_to_openai(result)

    assert len(schemas) == 2

    assert schemas[0]["function"]["name"] == "read_file"
    assert (
        schemas[0]["function"]["description"]
        == "Read a file"
    )

    assert schemas[1]["function"]["name"] == "list_directory"
    assert (
        schemas[1]["function"]["description"]
        == "List directory contents"
    )


def test_empty_tools_returns_empty_list() -> None:
    result = SimpleNamespace(
        tools=[]
    )

    schemas = mcp_tools_to_openai(result)

    assert schemas == []


def test_missing_description_becomes_empty_string() -> None:
    tool = SimpleNamespace(
        name="test_tool",
        description=None,
        inputSchema={
            "type": "object",
            "properties": {},
        },
    )

    result = SimpleNamespace(
        tools=[tool]
    )

    schemas = mcp_tools_to_openai(result)

    assert (
        schemas[0]["function"]["description"]
        == ""
    )


def test_empty_input_schema_gets_default_schema() -> None:
    tool = SimpleNamespace(
        name="test_tool",
        description="Test tool",
        inputSchema=None,
    )

    result = SimpleNamespace(
        tools=[tool]
    )

    schemas = mcp_tools_to_openai(result)

    assert (
        schemas[0]["function"]["parameters"]
        == {
            "type": "object",
            "properties": {},
        }
    )


def test_preserves_input_schema() -> None:
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
            },
            "limit": {
                "type": "integer",
            },
        },
        "required": ["query"],
    }

    tool = SimpleNamespace(
        name="search",
        description="Search",
        inputSchema=input_schema,
    )

    result = SimpleNamespace(
        tools=[tool]
    )

    schemas = mcp_tools_to_openai(result)

    assert (
        schemas[0]["function"]["parameters"]
        is input_schema
    )
