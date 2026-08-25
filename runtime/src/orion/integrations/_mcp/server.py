# integrations/mcp/server.py

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import Any


from mcp import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    stdio_client,
    get_default_environment,
)
from typing_extensions import override

from mcp.client.streamable_http import streamable_http_client
from orion.integrations._mcp.config import MCPServerConfig
from orion.runtime.lifecycle import Lifecycle


class MCPServer(Lifecycle):
    """
    Represents a single running MCP server.
    """

    def __init__(
        self,
        config: MCPServerConfig,
    ) -> None:
        self.config: MCPServerConfig = config

        self._stack: AsyncExitStack = AsyncExitStack()
        self._session: ClientSession | None = None
        self._connected: bool = False

    # =================================================
    # Properties
    # =================================================


    @property
    def name(self) -> str:
        return self.config.name

    @property
    def connected(self) -> bool:
        return self._connected


    # =================================================
    # Lifecycle
    # =================================================


    @override
    async def startup(self) -> None:
        if self._connected:
            return

        if self.config.transport == "stdio":
            await self._startup_stdio()
        elif self.config.transport == "http":
            await self._startup_http()

        else:
            raise ValueError(
                f"Unsupported MCP transport "
                f"'{self.config.transport}'"
                f"for server '{self.name}'"
            )

        self._connected = True

    @override
    async def shutdown(self) -> None:
        """
        Gracefully shut down the MCP server.

        Internal state is reset even if the underlying transport
        fails to close cleanly.
        """

        if not self._connected:
            return

        try:
            await self._stack.aclose()

        finally:
            self._session = None
            self._connected = False
            self._stack = AsyncExitStack()

    # =================================================
    # Startup stdio
    # =================================================

    async def _startup_stdio(self) -> None:
        """
        Start the stdio stream for the MCP server.
        """

        if not self.config.command:
            raise ValueError(
                f"MCP Server '{self.name}' uses stdio "
                "but no command was configured"
            )

        params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env= {
                **get_default_environment(),
                **(self.config.env or {}),
            }
        )

        read_stream, write_stream = (
            await self._stack.enter_async_context(
                stdio_client(params)
            )
        )

        self._session = await self._create_session(
            read_stream,
            write_stream,
        )

    # =================================================
    # Startup HTTP
    # =================================================


    async def _startup_http(self) -> None:
        """
        Start an MCP connection over HTTP.

        The concrete HTTP transport implementation will be added
        here using the MCP SDK's HTTP client transport.
        """

        if not self.config.url:
            raise ValueError(
                f"MCP Server '{self.name}' uses HTTP "
                "but no URL was configured"
            )

        read_stream, write_stream, _ = (
            await self._stack.enter_async_context(
                streamable_http_client(
                    self.config.url,
                )
            )
        )

        self._session = await self._create_session(read_stream, write_stream)

    # =================================================
    # Session Management
    # =================================================

    async def _create_session(
        self,
        read_stream,
        write_stream,
    ) -> ClientSession:
        """
        Create and initialize a new MCP client session.
        """

        session = await self._stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
            )
        )

        await session.initialize()
        return session

    # =================================================
    # MCP Operations
    # =================================================

    async def list_tools(self):
        """
        List all available tools on the MCP server.
        """

        if self._session is None:
            raise RuntimeError(
                f"MCP Server '{self.name}' is not connected"
            )

        return await self._session.list_tools()


    async def call_tool(self, name: str, arguments: dict[str, object]):
        """
        Call a tool on the MCP server.
        """

        if self._session is None:
            raise RuntimeError(
                f"MCP Server '{self.name}' is not connected"
            )

        return await self._session.call_tool(name, arguments)
