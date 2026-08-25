# runtime/src/orion/integrations/_mcp/manager.py

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from rich.console import Console
from typing_extensions import override

from orion.bus.event_bus import EventBus
from orion.integrations._mcp.config import MCPConfig
from orion.integrations._mcp.discovery import mcp_tools_to_openai
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
from orion.integrations._mcp.server import MCPServer
from orion.runtime.lifecycle import Lifecycle


console = Console()


class MCPManager(Lifecycle):
    """
    Manages all configured MCP servers.

    Responsibilities:
    - Start and stop MCP servers.
    - Discover tools exposed by connected servers.
    - Maintain tool -> server routing.
    - Execute MCP tools.
    - Expose discovered tool schemas to the agent.
    - Publish MCP lifecycle and execution events.

    MCPManager is transport- and server-agnostic.
    """

    SOURCE = "mcp_manager"

    def __init__(
        self,
        config: MCPConfig,
    ) -> None:
        self._config = config

        # EventBus is a process-wide singleton.
        # It must already be initialized by the application runtime.
        self._bus = EventBus()

        self._servers: dict[str, MCPServer] = {}

        # MCP tool name -> owning MCP server name.
        self._tool_routing: dict[str, str] = {}

        # OpenAI/Groq-compatible tool schemas.
        self._tools: list[dict[str, Any]] = []

        self._started = False

    # ==========================================================
    # Properties
    # ==========================================================

    @property
    def servers(self) -> dict[str, MCPServer]:
        """
        Return all successfully connected MCP servers.
        """
        return self._servers

    @property
    def tools(self) -> list[dict[str, Any]]:
        """
        Return all discovered MCP tools in
        OpenAI/Groq-compatible format.
        """
        return self._tools

    @property
    def started(self) -> bool:
        """
        Whether the manager has been started.
        """
        return self._started

    # ==========================================================
    # Lifecycle
    # ==========================================================

    @override
    async def startup(self) -> None:
        """
        Start all enabled MCP servers and discover their tools.

        Failure of one MCP server does not prevent other configured
        servers from starting.
        """

        if self._started:
            return

        console.print(
            "[cyan]Starting MCP servers...[/]"
        )

        for server_config in self._config.servers:

            if not server_config.enabled:
                console.print(
                    f"[dim]Skipping disabled MCP server "
                    f"'{server_config.name}'.[/]"
                )
                continue

            server = MCPServer(server_config)

            # --------------------------------------------------
            # Start server
            # --------------------------------------------------

            try:
                await server.startup()

            except Exception as exc:
                console.print(
                    f"[red]✗ MCP server "
                    f"'{server_config.name}' failed to start:[/] "
                    f"{exc}"
                )

                await self._bus.publish(
                    MCPServerStartupFailedEvent(
                        correlation_id=None,
                        session_id=None,
                        source=self.SOURCE,
                        message="MCP server startup failed.",
                        server_name=server_config.name,
                        transport=server_config.transport,
                        error=str(exc),
                    )
                )

                continue

            self._servers[server.name] = server

            console.print(
                f"[green]✓ MCP server "
                f"'{server.name}' connected "
                f"({server_config.transport}).[/]"
            )

            await self._bus.publish(
                MCPServerStartedEvent(
                    correlation_id=None,
                    session_id=None,
                    source=self.SOURCE,
                    message="MCP server started.",
                    server_name=server.name,
                    transport=server_config.transport,
                )
            )

            # --------------------------------------------------
            # Discover tools
            # --------------------------------------------------

            try:
                result = await server.list_tools()

                schemas = mcp_tools_to_openai(result)

            except Exception as exc:
                console.print(
                    f"[red]✗ Failed to discover tools "
                    f"from '{server.name}':[/] {exc}"
                )

                await self._bus.publish(
                    MCPToolsDiscoveryFailedEvent(
                        correlation_id=None,
                        session_id=None,
                        source=self.SOURCE,
                        message="MCP tool discovery failed.",
                        server_name=server.name,
                        error=str(exc),
                    )
                )

                continue

            discovered_names: list[str] = []

            for schema in schemas:

                function = cast(
                    dict[str, Any],
                    schema.get("function", {}),
                )

                tool_name = function.get("name")

                if not isinstance(tool_name, str):
                    continue

                # --------------------------------------------------
                # Duplicate protection
                # --------------------------------------------------

                if tool_name in self._tool_routing:
                    existing_server = self._tool_routing[tool_name]

                    console.print(
                        f"[yellow]⚠ MCP tool "
                        f"'{tool_name}' from '{server.name}' "
                        f"was ignored because it is already owned "
                        f"by '{existing_server}'.[/]"
                    )

                    continue

                self._tool_routing[tool_name] = server.name
                self._tools.append(schema)
                discovered_names.append(tool_name)

            console.print(
                f"[green]✓ Discovered "
                f"{len(discovered_names)} tools "
                f"from '{server.name}'.[/]"
            )

            await self._bus.publish(
                MCPToolsDiscoveredEvent(
                    correlation_id=None,
                    session_id=None,
                    source=self.SOURCE,
                    message="MCP tools discovered.",
                    server_name=server.name,
                    tool_names=discovered_names,
                    tool_count=len(discovered_names),
                )
            )

        self._started = True

        console.print(
            f"[green]MCP startup complete: "
            f"{len(self._servers)} server(s), "
            f"{len(self._tools)} tool(s).[/]"
        )

    @override
    async def shutdown(self) -> None:
        """
        Gracefully shut down all connected MCP servers.
        """

        if not self._started and not self._servers:
            return

        console.print(
            "[cyan]Stopping MCP servers...[/]"
        )

        for server_name, server in list(
            self._servers.items()
        ):
            try:
                await server.shutdown()

            except Exception as exc:
                console.print(
                    f"[red]✗ MCP server "
                    f"'{server_name}' failed to shut down:[/] "
                    f"{exc}"
                )

                await self._bus.publish(
                    MCPServerShutdownFailedEvent(
                        correlation_id=None,
                        session_id=None,
                        source=self.SOURCE,
                        message="MCP server shutdown failed.",
                        server_name=server_name,
                        error=str(exc),
                    )
                )

                continue

            console.print(
                f"[green]✓ MCP server "
                f"'{server_name}' stopped.[/]"
            )

            await self._bus.publish(
                MCPServerStoppedEvent(
                    correlation_id=None,
                    session_id=None,
                    source=self.SOURCE,
                    message="MCP server stopped.",
                    server_name=server_name,
                )
            )

        self._servers.clear()
        self._tool_routing.clear()
        self._tools.clear()

        self._started = False

        console.print(
            "[green]MCP shutdown complete.[/]"
        )

    # ==========================================================
    # Server Access
    # ==========================================================

    def server(
        self,
        name: str,
    ) -> MCPServer:
        """
        Return a connected MCP server by name.
        """

        try:
            return self._servers[name]

        except KeyError:
            raise ValueError(
                f"Unknown MCP server: {name}"
            ) from None

    # ==========================================================
    # Tool Execution
    # ==========================================================

    async def call_tool_raw(
        self,
        name: str,
        arguments: dict[str, object],
        *,
        session_id: UUID,
        correlation_id: UUID,
    ) -> object:
        """
        Route an MCP tool call to its owning server.

        Returns the raw MCP result.
        """

        server_name = self._tool_routing.get(name)

        if server_name is None:
            raise ValueError(
                f"Unknown MCP tool: {name}"
            )

        server = self._servers.get(server_name)

        if server is None:
            raise RuntimeError(
                f"MCP server '{server_name}' "
                f"owning tool '{name}' is not connected"
            )

        await self._bus.publish(
            MCPToolCalledEvent(
                correlation_id=correlation_id,
                session_id=session_id,
                source=self.SOURCE,
                message="MCP tool execution started.",
                server_name=server_name,
                tool_name=name,
            )
        )

        console.print(
            f"[cyan]→ MCP tool "
            f"'{name}' "
            f"({server_name})[/]"
        )

        try:
            result = await server.call_tool(
                name,
                arguments,
            )

        except Exception as exc:
            console.print(
                f"[red]✗ MCP tool "
                f"'{name}' failed:[/] {exc}"
            )

            await self._bus.publish(
                MCPToolFailedEvent(
                    correlation_id=correlation_id,
                    session_id=session_id,
                    source=self.SOURCE,
                    message="MCP tool execution failed.",
                    server_name=server_name,
                    tool_name=name,
                    error=str(exc),
                )
            )

            raise

        await self._bus.publish(
            MCPToolCompletedEvent(
                correlation_id=correlation_id,
                session_id=session_id,
                source=self.SOURCE,
                message="MCP tool execution completed.",
                server_name=server_name,
                tool_name=name,
            )
        )

        console.print(
            f"[green]✓ MCP tool "
            f"'{name}' completed.[/]"
        )

        return result

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, object],
        *,
        session_id: UUID,
        correlation_id: UUID,
    ) -> str:
        """
        Execute an MCP tool and flatten textual content into a string.
        """

        result = await self.call_tool_raw(
            name,
            arguments,
            session_id=session_id,
            correlation_id=correlation_id,
        )

        content = cast(
            list[object],
            getattr(result, "content", []),
        )

        parts: list[str] = []

        for item in content:
            text = cast(
                str | None,
                getattr(item, "text", None),
            )

            if text is not None:
                parts.append(text)

        return (
            "\n".join(parts)
            if parts
            else "(no output)"
        )
