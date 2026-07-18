# integrations/_mcp/manager.py

from __future__ import annotations

from integrations._mcp.config import MCPConfig
from integrations._mcp.server import MCPServer


class MCPManager:
    """
    Manages the lifecycle of all configured MCP servers.
    """

    def __init__(
        self,
        config: MCPConfig,
    ) -> None:
        self._config = config
        self._servers: dict[str, MCPServer] = {}

    async def startup(self) -> None:
        """
        Starts up all configured MCP servers.
        """
        for server_config in self._config.servers:
            if not server_config.enabled:
                continue

            server = MCPServer(server_config)

            await server.startup()

            self._servers[server.name] = server

    async def shutdown(self) -> None:
        """
        Shuts down all configured MCP servers.
        """
        for server in self._servers.values():
            await server.shutdown()

        self._servers.cofi