"""
Client session implementation.

A ClientSession represents a single active IPC connection between an
Orion client and the runtime. It provides high-level methods for sending
and receiving protocol messages while hiding the underlying socket
implementation.

The session is responsible only for transport. It does not interpret
messages or perform any business logic.
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

from .messages import Envelope
from .protocol import decode, encode


class ClientSession:
    """
    Represents one connected IPC client.

    Each session owns exactly one pair of asyncio streams and is
    responsible for transmitting protocol messages over them.
    """

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Create a new client session.

        Args:
            reader:
                Stream used to receive data.

            writer:
                Stream used to send data.
        """
        self.id: UUID = uuid4()
        self._reader = reader
        self._writer = writer

    @property
    def closed(self) -> bool:
        """
        Whether the client connection has been closed.
        """
        return self._writer.is_closing()

    async def send(self, message: Envelope) -> None:
        """
        Send a protocol message to the client.

        Args:
            message:
                Message to transmit.
        """
        self._writer.write(encode(message))
        await self._writer.drain()

    async def receive(self) -> Envelope:
        """
        Receive the next protocol message.

        Returns:
            The decoded protocol message.

        Raises:
            ConnectionError:
                If the remote peer closes the connection.
        """
        data = await self._reader.readline()

        if not data:
            raise ConnectionError("Client disconnected.")

        return decode(data)

    async def close(self) -> None:
        """
        Close the client session.
        """
        self._writer.close()
        await self._writer.wait_closed()

    async def __aenter__(self) -> "ClientSession":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, closed={self.closed})"
