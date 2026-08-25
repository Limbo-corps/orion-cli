from __future__ import annotations

from orion.events.base import Event, EventStatus


# ==========================================================
# Server Lifecycle
# ==========================================================


class MCPServerStartedEvent(Event):
    """
    Published when an MCP server successfully connects.
    """

    status: EventStatus = EventStatus.SUCCESS

    server_name: str
    transport: str


class MCPServerStartupFailedEvent(Event):
    """
    Published when an MCP server fails to start.
    """

    status: EventStatus = EventStatus.ERROR

    server_name: str
    transport: str
    error: str


class MCPServerStoppedEvent(Event):
    """
    Published when an MCP server is shut down successfully.
    """

    status: EventStatus = EventStatus.SUCCESS

    server_name: str


class MCPServerShutdownFailedEvent(Event):
    """
    Published when an MCP server fails to shut down.
    """

    status: EventStatus = EventStatus.ERROR

    server_name: str
    error: str


# ==========================================================
# Tool Discovery
# ==========================================================


class MCPToolsDiscoveredEvent(Event):
    """
    Published after an MCP server's tools have been
    successfully discovered.
    """

    status: EventStatus = EventStatus.SUCCESS

    server_name: str
    tool_names: list[str]
    tool_count: int


class MCPToolsDiscoveryFailedEvent(Event):
    """
    Published when tool discovery fails for an MCP server.
    """

    status: EventStatus = EventStatus.ERROR

    server_name: str
    error: str


# ==========================================================
# Tool Execution
# ==========================================================


class MCPToolCalledEvent(Event):
    """
    Published immediately before an MCP tool is executed.

    This is request-scoped and therefore carries the
    session and correlation identifiers inherited from Event.
    """

    status: EventStatus = EventStatus.INFO

    server_name: str
    tool_name: str


class MCPToolCompletedEvent(Event):
    """
    Published after an MCP tool completes successfully.

    This is request-scoped.
    """

    status: EventStatus = EventStatus.SUCCESS

    server_name: str
    tool_name: str


class MCPToolFailedEvent(Event):
    """
    Published when an MCP tool execution fails.

    This is request-scoped.
    """

    status: EventStatus = EventStatus.ERROR

    server_name: str
    tool_name: str
    error: str
