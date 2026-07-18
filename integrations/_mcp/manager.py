# integrations/_mcp/manager.py

from __future__ import annotations

from typing import Any

from integrations._mcp.config import MCPConfig
from integrations._mcp.server import MCPServer
from integrations._mcp.discovery import mcp_tools_to_openai

class MCPManager:
    """
    Manages the lifecycle of all configured MCP servers and exposes their
    tools to the agent in an OpenAI/Groq-compatible format.
    """

    def __init__(
        self,
        config: MCPConfig,
    ) -> None:
        self._config = config
        self._servers: dict[str, MCPServer] = {}
        self._tool_routing: dict[str, str] = {}
        self._tools: list[dict[str, Any]] = []

    async def startup(self) -> None:
        """
        Start every enabled MCP server and collect its tools.
        A failing server is skipped, not fatal to the pipeline.
        """
        for server_config in self._config.servers:
            if not server_config.enabled:
                continue

            server = MCPServer(server_config)
            try:
                await server.startup()
            except Exception as e:
                print(f"[mcp] failed to start '{server_config.name}': {e}")
                continue

            self._servers[server.name] = server
            
            result = await server.list_tools()
            for schema in mcp_tools_to_openai(result):
                tool_name = schema["function"]["name"]
                self._tool_routing[tool_name] = server.name
                self._tools.append(schema)

    @property
    def tools(self) -> list[dict[str, Any]]:
        """OpenAI/Groq tool schemas for every connected server."""
        return self._tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Route a tool call to the server that owns it and flatten the result to text."""
        server_name = self._tool_routing.get(name)
        if server_name is None:
            return f"Error: unknown tool '{name}'"

        result = await self._servers[server_name].call_tool(name, arguments)

        parts = []
        for item in getattr(result, "content", []) or []:
            text = getattr(item, "text", None)
            if text is not None:
                parts.append(text)

        return "\n".join(parts) if parts else "(no output)"


    async def shutdown(self) -> None:
        """
        Shuts down all configured MCP servers.
        """
        for server in self._servers.values():
            await server.shutdown()

        self._servers.clear() 
