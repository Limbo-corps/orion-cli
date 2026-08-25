# runtime/tests/integrations/test_mcp_server.py

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orion.integrations._mcp.config import MCPServerConfig
from orion.integrations._mcp.server import MCPServer


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def stdio_config() -> MCPServerConfig:
    return MCPServerConfig(
        name="filesystem",
        transport="stdio",
        command="npx",
        args=["-y", "test-mcp-server"],
        env={"TEST_ENV": "true"},
    )


@pytest.fixture
def http_config() -> MCPServerConfig:
    return MCPServerConfig(
        name="neo4j-mcp",
        transport="http",
        url="https://example.mcp.neo4j.io",
    )


@pytest.fixture
def server(
    stdio_config: MCPServerConfig,
) -> MCPServer:
    return MCPServer(stdio_config)


# ==========================================================
# Properties
# ==========================================================


def test_name(
    server: MCPServer,
) -> None:
    assert server.name == "filesystem"


def test_connected_initially_false(
    server: MCPServer,
) -> None:
    assert server.connected is False


# ==========================================================
# Startup - stdio
# ==========================================================


@pytest.mark.asyncio
async def test_startup_stdio(
    stdio_config: MCPServerConfig,
) -> None:

    server = MCPServer(stdio_config)

    mock_read_stream = MagicMock()
    mock_write_stream = MagicMock()

    mock_session = AsyncMock()

    with (
        patch(
            "orion.integrations._mcp.server.stdio_client"
        ) as mock_stdio_client,
        patch.object(
            server,
            "_create_session",
            new=AsyncMock(return_value=mock_session),
        ) as mock_create_session,
    ):
        mock_stdio_client.return_value.__aenter__ = AsyncMock(
            return_value=(
                mock_read_stream,
                mock_write_stream,
            )
        )
        mock_stdio_client.return_value.__aexit__ = AsyncMock()

        await server.startup()

    assert server.connected is True

    mock_stdio_client.assert_called_once()

    mock_create_session.assert_awaited_once_with(
        mock_read_stream,
        mock_write_stream,
    )


@pytest.mark.asyncio
async def test_startup_stdio_requires_command() -> None:

    config = MCPServerConfig(
        name="invalid",
        transport="stdio",
        command=None,
    )

    server = MCPServer(config)

    with pytest.raises(
        ValueError,
        match="uses stdio but no command was configured",
    ):
        await server.startup()

    assert server.connected is False


# ==========================================================
# Startup - HTTP
# ==========================================================


@pytest.mark.asyncio
async def test_startup_http(
    http_config: MCPServerConfig,
) -> None:

    server = MCPServer(http_config)

    mock_read_stream = MagicMock()
    mock_write_stream = MagicMock()

    mock_session = AsyncMock()

    with (
        patch(
            "orion.integrations._mcp.server.streamable_http_client"
        ) as mock_http_client,
        patch.object(
            server,
            "_create_session",
            new=AsyncMock(return_value=mock_session),
        ) as mock_create_session,
    ):
        mock_http_client.return_value.__aenter__ = AsyncMock(
            return_value=(
                mock_read_stream,
                mock_write_stream,
                MagicMock(),
            )
        )
        mock_http_client.return_value.__aexit__ = AsyncMock()

        await server.startup()

    assert server.connected is True

    mock_http_client.assert_called_once_with(
        "https://example.mcp.neo4j.io"
    )

    mock_create_session.assert_awaited_once_with(
        mock_read_stream,
        mock_write_stream,
    )


@pytest.mark.asyncio
async def test_startup_http_requires_url() -> None:

    config = MCPServerConfig(
        name="invalid",
        transport="http",
        url=None,
    )

    server = MCPServer(config)

    with pytest.raises(
        ValueError,
        match="uses HTTP but no URL was configured",
    ):
        await server.startup()

    assert server.connected is False


# ==========================================================
# Unsupported Transport
# ==========================================================


@pytest.mark.asyncio
async def test_startup_rejects_unsupported_transport() -> None:

    config = MCPServerConfig(
        name="invalid",
        transport="stdio",
        command="echo",
    )

    server = MCPServer(config)

    # Bypass the Literal type at runtime to verify
    # the defensive branch in startup().
    server.config = MagicMock(
        name="invalid",
        transport="websocket",
        command=None,
        args=[],
        env={},
        url=None,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported MCP transport 'websocket'",
    ):
        await server.startup()

    assert server.connected is False


# ==========================================================
# Startup Idempotency
# ==========================================================


@pytest.mark.asyncio
async def test_startup_does_nothing_when_already_connected(
    server: MCPServer,
) -> None:

    server._connected = True

    with patch.object(
        server,
        "_startup_stdio",
        new=AsyncMock(),
    ) as startup_stdio:

        await server.startup()

    startup_stdio.assert_not_awaited()
    assert server.connected is True


# ==========================================================
# Session Creation
# ==========================================================


@pytest.mark.asyncio
async def test_create_session(
    server: MCPServer,
) -> None:

    mock_read_stream = MagicMock()
    mock_write_stream = MagicMock()

    mock_session = AsyncMock()

    # The AsyncExitStack enters ClientSession as a context manager.
    server._stack.enter_async_context = AsyncMock(
        return_value=mock_session
    )

    result = await server._create_session(
        mock_read_stream,
        mock_write_stream,
    )

    assert result is mock_session

    mock_session.initialize.assert_awaited_once()

    server._stack.enter_async_context.assert_awaited_once()


# ==========================================================
# list_tools()
# ==========================================================


@pytest.mark.asyncio
async def test_list_tools_requires_connection(
    server: MCPServer,
) -> None:

    with pytest.raises(
        RuntimeError,
        match="is not connected",
    ):
        await server.list_tools()


@pytest.mark.asyncio
async def test_list_tools(
    server: MCPServer,
) -> None:

    mock_session = AsyncMock()

    expected = MagicMock()

    mock_session.list_tools.return_value = expected

    server._session = mock_session
    server._connected = True

    result = await server.list_tools()

    assert result is expected

    mock_session.list_tools.assert_awaited_once()


# ==========================================================
# call_tool()
# ==========================================================


@pytest.mark.asyncio
async def test_call_tool_requires_connection(
    server: MCPServer,
) -> None:

    with pytest.raises(
        RuntimeError,
        match="is not connected",
    ):
        await server.call_tool(
            "test_tool",
            {"value": "hello"},
        )


@pytest.mark.asyncio
async def test_call_tool(
    server: MCPServer,
) -> None:

    mock_session = AsyncMock()

    expected = MagicMock()

    mock_session.call_tool.return_value = expected

    server._session = mock_session
    server._connected = True

    result = await server.call_tool(
        "test_tool",
        {"value": "hello"},
    )

    assert result is expected

    mock_session.call_tool.assert_awaited_once_with(
        "test_tool",
        {"value": "hello"},
    )


# ==========================================================
# Shutdown
# ==========================================================


@pytest.mark.asyncio
async def test_shutdown_when_not_connected(
    server: MCPServer,
) -> None:

    server._connected = False

    server._stack.aclose = AsyncMock()

    await server.shutdown()

    server._stack.aclose.assert_not_awaited()


@pytest.mark.asyncio
async def test_shutdown(
    server: MCPServer,
) -> None:

    server._connected = True
    server._session = MagicMock()

    old_stack = server._stack
    old_stack.aclose = AsyncMock()

    await server.shutdown()

    old_stack.aclose.assert_awaited_once()

    assert server.connected is False
    assert server._session is None

    # A fresh stack is created so the server can be started again.
    assert server._stack is not old_stack


@pytest.mark.asyncio
async def test_shutdown_cleans_state_when_stack_close_fails(
    server: MCPServer,
) -> None:

    server._connected = True
    server._session = MagicMock()

    old_stack = server._stack

    old_stack.aclose = AsyncMock(
        side_effect=RuntimeError("close failed")
    )

    with pytest.raises(
        RuntimeError,
        match="close failed",
    ):
        await server.shutdown()

    assert server.connected is False
    assert server._session is None
    assert server._stack is not old_stack
