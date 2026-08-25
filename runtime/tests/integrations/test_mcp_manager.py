# runtime/tests/integrations/test_mcp_manager.py

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from orion.bus.event_bus import EventBus
from orion.core.singleton import SingletonMeta
from orion.integrations._mcp.config import MCPConfig, MCPServerConfig
from orion.integrations._mcp.events import (
    MCPServerShutdownFailedEvent,
    MCPServerStartedEvent,
    MCPServerStartupFailedEvent,
    MCPServerStoppedEvent,
    MCPToolCalledEvent,
    MCPToolCompletedEvent,
    MCPToolFailedEvent,
    MCPToolsDiscoveredEvent,
    MCPToolsDiscoveryFailedEvent,
)
from orion.integrations._mcp.manager import MCPManager
from orion.integrations._mcp.server import MCPServer


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture(autouse=True)
def reset_event_bus():
    """
    Reset the EventBus singleton between tests.

    EventBus is process-wide and therefore must not leak
    subscribers or stores between tests.
    """

    SingletonMeta._instances.pop(EventBus, None)

    yield

    SingletonMeta._instances.pop(EventBus, None)


@pytest.fixture
def event_bus() -> EventBus:
    """
    Create the global EventBus with a mocked event store.
    """

    store = MagicMock()
    store.append = AsyncMock()

    return EventBus(store)


@pytest.fixture
def config() -> MCPConfig:
    return MCPConfig(
        servers=[
            MCPServerConfig(
                name="filesystem",
                transport="stdio",
                command="npx",
            ),
        ]
    )


@pytest.fixture
def manager(
    config: MCPConfig,
    event_bus: EventBus,
) -> MCPManager:
    """
    EventBus must exist before MCPManager is constructed.
    """

    return MCPManager(config)


# ==========================================================
# Helpers
# ==========================================================


async def collect_events(
    event_bus: EventBus,
) -> list[object]:
    """
    Subscribe to every event and return the collected list.
    """

    events: list[object] = []

    async def capture(event: object) -> None:
        events.append(event)

    event_bus.subscribe_all(capture)

    return events


# ==========================================================
# Properties
# ==========================================================


def test_servers_initially_empty(
    manager: MCPManager,
) -> None:
    assert manager.servers == {}


def test_tools_initially_empty(
    manager: MCPManager,
) -> None:
    assert manager.tools == []


def test_started_initially_false(
    manager: MCPManager,
) -> None:
    assert manager.started is False


# ==========================================================
# Startup
# ==========================================================


@pytest.mark.asyncio
async def test_startup_connects_server_and_discovers_tools(
    manager: MCPManager,
    event_bus: EventBus,
) -> None:
    mock_server = MagicMock(spec=MCPServer)

    mock_server.name = "filesystem"
    mock_server.startup = AsyncMock()
    mock_server.list_tools = AsyncMock(
        return_value=MagicMock()
    )

    schemas = [
        {
            "type": "function",
            "function": {
                "name": "read_text_file",
                "description": "Read a file",
                "parameters": {},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List a directory",
                "parameters": {},
            },
        },
    ]

    events = await collect_events(event_bus)

    with (
        patch(
            "orion.integrations._mcp.manager.MCPServer",
            return_value=mock_server,
        ),
        patch(
            "orion.integrations._mcp.manager.mcp_tools_to_openai",
            return_value=schemas,
        ),
    ):
        await manager.startup()

    assert manager.started is True
    assert manager.servers["filesystem"] is mock_server

    assert len(manager.tools) == 2
    assert (
        manager.tools[0]["function"]["name"]
        == "read_text_file"
    )
    assert (
        manager.tools[1]["function"]["name"]
        == "list_directory"
    )

    mock_server.startup.assert_awaited_once()
    mock_server.list_tools.assert_awaited_once()

    started = [
        event
        for event in events
        if isinstance(event, MCPServerStartedEvent)
    ]

    discovered = [
        event
        for event in events
        if isinstance(event, MCPToolsDiscoveredEvent)
    ]

    assert len(started) == 1
    assert started[0].server_name == "filesystem"
    assert started[0].transport == "stdio"

    assert len(discovered) == 1
    assert discovered[0].server_name == "filesystem"
    assert discovered[0].tool_count == 2
    assert discovered[0].tool_names == [
        "read_text_file",
        "list_directory",
    ]


@pytest.mark.asyncio
async def test_startup_skips_disabled_servers(
    event_bus: EventBus,
) -> None:
    config = MCPConfig(
        servers=[
            MCPServerConfig(
                name="disabled",
                command="echo",
                enabled=False,
            )
        ]
    )

    manager = MCPManager(config)

    with patch(
        "orion.integrations._mcp.manager.MCPServer"
    ) as mock_server:
        await manager.startup()

    mock_server.assert_not_called()

    assert manager.started is True
    assert manager.servers == {}
    assert manager.tools == []


@pytest.mark.asyncio
async def test_startup_failure_does_not_stop_other_servers(
    event_bus: EventBus,
) -> None:
    config = MCPConfig(
        servers=[
            MCPServerConfig(
                name="broken",
                command="broken",
            ),
            MCPServerConfig(
                name="working",
                command="working",
            ),
        ]
    )

    manager = MCPManager(config)

    broken_server = MagicMock(spec=MCPServer)
    broken_server.name = "broken"
    broken_server.startup = AsyncMock(
        side_effect=RuntimeError("connection failed")
    )

    working_server = MagicMock(spec=MCPServer)
    working_server.name = "working"
    working_server.startup = AsyncMock()
    working_server.list_tools = AsyncMock(
        return_value=MagicMock()
    )

    events = await collect_events(event_bus)

    with (
        patch(
            "orion.integrations._mcp.manager.MCPServer",
            side_effect=[
                broken_server,
                working_server,
            ],
        ),
        patch(
            "orion.integrations._mcp.manager.mcp_tools_to_openai",
            return_value=[],
        ),
    ):
        await manager.startup()

    assert manager.started is True

    assert "broken" not in manager.servers
    assert "working" in manager.servers

    failures = [
        event
        for event in events
        if isinstance(
            event,
            MCPServerStartupFailedEvent,
        )
    ]

    assert len(failures) == 1
    assert failures[0].server_name == "broken"
    assert failures[0].transport == "stdio"
    assert failures[0].error == "connection failed"

    assert failures[0].correlation_id is None
    assert failures[0].session_id is None


# ==========================================================
# Tool Discovery Failure
# ==========================================================


@pytest.mark.asyncio
async def test_tool_discovery_failure_publishes_event(
    manager: MCPManager,
    event_bus: EventBus,
) -> None:
    mock_server = MagicMock(spec=MCPServer)

    mock_server.name = "filesystem"
    mock_server.startup = AsyncMock()
    mock_server.list_tools = AsyncMock(
        side_effect=RuntimeError("discovery failed")
    )

    events = await collect_events(event_bus)

    with patch(
        "orion.integrations._mcp.manager.MCPServer",
        return_value=mock_server,
    ):
        await manager.startup()

    assert "filesystem" in manager.servers
    assert manager.tools == []

    failures = [
        event
        for event in events
        if isinstance(
            event,
            MCPToolsDiscoveryFailedEvent,
        )
    ]

    assert len(failures) == 1
    assert failures[0].server_name == "filesystem"
    assert failures[0].error == "discovery failed"

    # Discovery is a lifecycle operation, not request-scoped.
    assert failures[0].correlation_id is None
    assert failures[0].session_id is None


# ==========================================================
# Duplicate Tools
# ==========================================================


@pytest.mark.asyncio
async def test_duplicate_tool_is_rejected(
    event_bus: EventBus,
) -> None:
    config = MCPConfig(
        servers=[
            MCPServerConfig(
                name="server_a",
                command="a",
            ),
            MCPServerConfig(
                name="server_b",
                command="b",
            ),
        ]
    )

    manager = MCPManager(config)

    server_a = MagicMock(spec=MCPServer)
    server_a.name = "server_a"
    server_a.startup = AsyncMock()
    server_a.list_tools = AsyncMock(
        return_value=MagicMock()
    )

    server_b = MagicMock(spec=MCPServer)
    server_b.name = "server_b"
    server_b.startup = AsyncMock()
    server_b.list_tools = AsyncMock(
        return_value=MagicMock()
    )

    schemas = [
        {
            "type": "function",
            "function": {
                "name": "same_tool",
                "description": "Duplicate",
                "parameters": {},
            },
        }
    ]

    with (
        patch(
            "orion.integrations._mcp.manager.MCPServer",
            side_effect=[
                server_a,
                server_b,
            ],
        ),
        patch(
            "orion.integrations._mcp.manager.mcp_tools_to_openai",
            return_value=schemas,
        ),
    ):
        await manager.startup()

    # First server owns the tool.
    assert len(manager.tools) == 1
    assert (
        manager.tools[0]["function"]["name"]
        == "same_tool"
    )
    assert (
        manager._tool_routing["same_tool"]
        == "server_a"
    )


# ==========================================================
# Startup Idempotency
# ==========================================================


@pytest.mark.asyncio
async def test_startup_only_runs_once(
    manager: MCPManager,
    event_bus: EventBus,
) -> None:
    mock_server = MagicMock(spec=MCPServer)

    mock_server.name = "filesystem"
    mock_server.startup = AsyncMock()
    mock_server.list_tools = AsyncMock(
        return_value=MagicMock()
    )

    with (
        patch(
            "orion.integrations._mcp.manager.MCPServer",
            return_value=mock_server,
        ),
        patch(
            "orion.integrations._mcp.manager.mcp_tools_to_openai",
            return_value=[],
        ),
    ):
        await manager.startup()
        await manager.startup()

    mock_server.startup.assert_awaited_once()


# ==========================================================
# Server Access
# ==========================================================


def test_server_returns_connected_server(
    manager: MCPManager,
) -> None:
    mock_server = MagicMock(spec=MCPServer)

    manager._servers["filesystem"] = mock_server

    assert manager.server("filesystem") is mock_server


def test_server_unknown_name_raises(
    manager: MCPManager,
) -> None:
    with pytest.raises(
        ValueError,
        match="Unknown MCP server: missing",
    ):
        manager.server("missing")


# ==========================================================
# Raw Tool Execution
# ==========================================================


@pytest.mark.asyncio
async def test_call_tool_raw(
    manager: MCPManager,
    event_bus: EventBus,
) -> None:
    mock_server = MagicMock(spec=MCPServer)

    mock_result = MagicMock()

    mock_server.call_tool = AsyncMock(
        return_value=mock_result
    )

    manager._servers["filesystem"] = mock_server
    manager._tool_routing["read_file"] = "filesystem"

    session_id = uuid4()
    correlation_id = uuid4()

    events = await collect_events(event_bus)

    result = await manager.call_tool_raw(
        "read_file",
        {"path": "test.txt"},
        session_id=session_id,
        correlation_id=correlation_id,
    )

    assert result is mock_result

    mock_server.call_tool.assert_awaited_once_with(
        "read_file",
        {"path": "test.txt"},
    )

    called = [
        event
        for event in events
        if isinstance(
            event,
            MCPToolCalledEvent,
        )
    ]

    completed = [
        event
        for event in events
        if isinstance(
            event,
            MCPToolCompletedEvent,
        )
    ]

    assert len(called) == 1
    assert len(completed) == 1

    assert called[0].server_name == "filesystem"
    assert called[0].tool_name == "read_file"
    assert called[0].session_id == session_id
    assert called[0].correlation_id == correlation_id

    assert completed[0].server_name == "filesystem"
    assert completed[0].tool_name == "read_file"
    assert completed[0].session_id == session_id
    assert completed[0].correlation_id == correlation_id


@pytest.mark.asyncio
async def test_call_tool_raw_unknown_tool(
    manager: MCPManager,
) -> None:
    with pytest.raises(
        ValueError,
        match="Unknown MCP tool: missing",
    ):
        await manager.call_tool_raw(
            "missing",
            {},
            session_id=uuid4(),
            correlation_id=uuid4(),
        )


# ==========================================================
# Tool Execution Failure
# ==========================================================


@pytest.mark.asyncio
async def test_call_tool_raw_failure_publishes_event(
    manager: MCPManager,
    event_bus: EventBus,
) -> None:
    mock_server = MagicMock(spec=MCPServer)

    mock_server.call_tool = AsyncMock(
        side_effect=RuntimeError("tool failed")
    )

    manager._servers["filesystem"] = mock_server
    manager._tool_routing["read_file"] = "filesystem"

    session_id = uuid4()
    correlation_id = uuid4()

    events = await collect_events(event_bus)

    with pytest.raises(
        RuntimeError,
        match="tool failed",
    ):
        await manager.call_tool_raw(
            "read_file",
            {},
            session_id=session_id,
            correlation_id=correlation_id,
        )

    failures = [
        event
        for event in events
        if isinstance(
            event,
            MCPToolFailedEvent,
        )
    ]

    assert len(failures) == 1

    assert failures[0].server_name == "filesystem"
    assert failures[0].tool_name == "read_file"
    assert failures[0].error == "tool failed"

    assert failures[0].session_id == session_id
    assert failures[0].correlation_id == correlation_id


# ==========================================================
# call_tool()
# ==========================================================


@pytest.mark.asyncio
async def test_call_tool_flattens_text(
    manager: MCPManager,
    event_bus: EventBus,
) -> None:
    mock_server = MagicMock(spec=MCPServer)

    text_one = MagicMock()
    text_one.text = "first"

    text_two = MagicMock()
    text_two.text = "second"

    result = MagicMock()
    result.content = [
        text_one,
        text_two,
    ]

    mock_server.call_tool = AsyncMock(
        return_value=result
    )

    manager._servers["filesystem"] = mock_server
    manager._tool_routing["read_file"] = "filesystem"

    output = await manager.call_tool(
        "read_file",
        {},
        session_id=uuid4(),
        correlation_id=uuid4(),
    )

    assert output == "first\nsecond"


@pytest.mark.asyncio
async def test_call_tool_returns_no_output(
    manager: MCPManager,
) -> None:
    mock_server = MagicMock(spec=MCPServer)

    result = MagicMock()
    result.content = []

    mock_server.call_tool = AsyncMock(
        return_value=result
    )

    manager._servers["filesystem"] = mock_server
    manager._tool_routing["empty_tool"] = "filesystem"

    output = await manager.call_tool(
        "empty_tool",
        {},
        session_id=uuid4(),
        correlation_id=uuid4(),
    )

    assert output == "(no output)"


# ==========================================================
# Shutdown
# ==========================================================


@pytest.mark.asyncio
async def test_shutdown_stops_servers(
    manager: MCPManager,
    event_bus: EventBus,
) -> None:
    server_one = MagicMock(spec=MCPServer)
    server_one.name = "one"
    server_one.shutdown = AsyncMock()

    server_two = MagicMock(spec=MCPServer)
    server_two.name = "two"
    server_two.shutdown = AsyncMock()

    manager._servers["one"] = server_one
    manager._servers["two"] = server_two

    manager._tool_routing["tool_one"] = "one"
    manager._tools.append(
        {
            "type": "function",
            "function": {
                "name": "tool_one",
            },
        }
    )

    manager._started = True

    events = await collect_events(event_bus)

    await manager.shutdown()

    server_one.shutdown.assert_awaited_once()
    server_two.shutdown.assert_awaited_once()

    assert manager.servers == {}
    assert manager.tools == []
    assert manager._tool_routing == {}
    assert manager.started is False

    stopped = [
        event
        for event in events
        if isinstance(
            event,
            MCPServerStoppedEvent,
        )
    ]

    assert len(stopped) == 2


@pytest.mark.asyncio
async def test_shutdown_failure_publishes_event(
    manager: MCPManager,
    event_bus: EventBus,
) -> None:
    mock_server = MagicMock(spec=MCPServer)
    mock_server.name = "filesystem"

    mock_server.shutdown = AsyncMock(
        side_effect=RuntimeError("shutdown failed")
    )

    manager._servers["filesystem"] = mock_server
    manager._started = True

    events = await collect_events(event_bus)

    # Shutdown failures are isolated and should not escape.
    await manager.shutdown()

    failures = [
        event
        for event in events
        if isinstance(
            event,
            MCPServerShutdownFailedEvent,
        )
    ]

    assert len(failures) == 1

    assert failures[0].server_name == "filesystem"
    assert failures[0].error == "shutdown failed"

    assert manager.servers == {}
    assert manager.tools == []
    assert manager.started is False
