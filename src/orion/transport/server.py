"""
IPC server implementation.

The IPC server listens for incoming client connections over a Unix Domain
Socket and creates a ClientSession for each connected client.

The server is responsible only for connection management. It delegates
all message processing to a user-provided session handler.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from pathlib import Path

from orion.runtime.lifecycle import Lifecycle

from .session import ClientSession

SessionHandler = Callable[[ClientSession], Awaitable[None]]


class IPCServer(Lifecycle):
    """
    Orion IPC server.

    The server accepts incoming Unix socket connections and creates a
    ClientSession for each client. Once connected, the supplied session
    handler is responsible for the lifetime of that session.
    """

    def __init__(
        self,
        socket_path: str | Path,
        session_handler: SessionHandler,
    ) -> None:
        """
        Create a new IPC server.

        Args:
            socket_path:
                Path to the Unix Domain Socket.

            session_handler:
                Coroutine invoked for each connected client.
        """
        self._socket_path = Path(socket_path)
        self._session_handler = session_handler

        self._server: asyncio.AbstractServer | None = None

    @property
    def is_running(self) -> bool:
        """
        Whether the server is currently accepting connections.
        """
        return self._server is not None

    async def startup(self) -> None:
        """
        Start accepting client connections.
        """
        if self._server is not None:
            raise RuntimeError("IPC server is already running.")

        with suppress(FileNotFoundError):
            self._socket_path.unlink()

        self._server = await asyncio.start_unix_server(
            self._accept_client,
            path=str(self._socket_path),
        )

    async def shutdown(self) -> None:
        """
        Stop accepting client connections.
        """
        if self._server is None:
            return

        try:
            self._server.close()
            await self._server.wait_closed()
        finally:
            self._server = None

            with suppress(FileNotFoundError):
                self._socket_path.unlink()

    async def serve_forever(self) -> None:
        """
        Run the server until cancelled.
        """
        if self._server is None:
            raise RuntimeError("IPC server has not been started.")

        async with self._server:
            await self._server.serve_forever()

    async def _accept_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Accept a newly connected client.

        Args:
            reader:
                Stream used to receive client messages.

            writer:
                Stream used to send client messages.
        """
        print(f"[IPC] Client connected: {reader}")
        session = ClientSession(reader, writer)

        try:
            await self._session_handler(session)
        finally:
            print(f"[IPC] Client disconnected: {reader}")
            await session.close()
