# integrations/mcp/server.py

from __future__ import annotations

from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    stdio_client,
)

from integrations._mcp.config import MCPServerConfig


class MCPServer:
    """
    Represents a single running MCP server.
    """

    def __init__(
        self,
        config: MCPServerConfig,
    ) -> None:
        self.config = config

        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self._connected = False

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def connected(self) -> bool:
        return self._connected

    async def startup(self) -> None:
        """
        Launch the server and establish an MCP session.
        """

        params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env=self.config.env,
        )

        read_stream, write_stream = await self._stack.enter_async_context(
            stdio_client(params)
        )

        session = await self._stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
            )
        )

        await session.initialize()

        self._session = session
        self._connected = True

    async def shutdown(self) -> None:
        """
        Close the MCP session.
        """

        await self._stack.aclose()

        self._session = None
        self._connected = False

    async def list_tools(self):
        if self._session is None:
            raise RuntimeError("MCP server is not connected.")

        return await self._session.list_tools()

    async def call_tool(
        self,
        name: str,
        arguments: dict,
    ):
        if self._session is None:
            raise RuntimeError("MCP server is not connected.")

        return await self._session.call_tool(
            name,
            arguments,
        )
