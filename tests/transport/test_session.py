from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from orion.transport.messages import Envelope, MessageType
from orion.transport.session import ClientSession


@pytest_asyncio.fixture
async def session_pair() -> tuple[ClientSession, ClientSession]:
    """
    Create a connected pair of ClientSession objects.
    """

    server_session: ClientSession | None = None
    connected = asyncio.Event()

    async def handler(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        nonlocal server_session

        server_session = ClientSession(reader, writer)
        connected.set()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)

    host, port = server.sockets[0].getsockname()

    reader, writer = await asyncio.open_connection(host, port)
    client_session = ClientSession(reader, writer)

    await connected.wait()

    assert server_session is not None

    try:
        yield client_session, server_session

    finally:
        await client_session.close()

        if not server_session.closed:
            await server_session.close()

        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_session_has_unique_id(
    session_pair: tuple[ClientSession, ClientSession],
) -> None:
    client, server = session_pair

    assert client.id != server.id


@pytest.mark.asyncio
async def test_send_message(
    session_pair: tuple[ClientSession, ClientSession],
) -> None:
    client, server = session_pair

    message = Envelope(
        type=MessageType.PING,
        payload={},
    )

    await client.send(message)

    received = await server.receive()

    assert received == message


@pytest.mark.asyncio
async def test_receive_message(
    session_pair: tuple[ClientSession, ClientSession],
) -> None:
    client, server = session_pair

    message = Envelope(
        type=MessageType.PONG,
        payload={},
    )

    await server.send(message)

    received = await client.receive()

    assert received == message


@pytest.mark.asyncio
async def test_send_multiple_messages(
    session_pair: tuple[ClientSession, ClientSession],
) -> None:
    client, server = session_pair

    messages = [
        Envelope(type=MessageType.PING, payload={}),
        Envelope(type=MessageType.PONG, payload={}),
        Envelope(type=MessageType.STATUS, payload={}),
    ]

    for message in messages:
        await client.send(message)

    for expected in messages:
        received = await server.receive()
        assert received == expected


@pytest.mark.asyncio
async def test_receive_closed_connection(
    session_pair: tuple[ClientSession, ClientSession],
) -> None:
    client, server = session_pair

    await server.close()

    with pytest.raises(ConnectionError):
        await client.receive()


@pytest.mark.asyncio
async def test_closed_property(
    session_pair: tuple[ClientSession, ClientSession],
) -> None:
    client, _ = session_pair

    assert not client.closed

    await client.close()

    assert client.closed


@pytest.mark.asyncio
async def test_close_is_idempotent(
    session_pair: tuple[ClientSession, ClientSession],
) -> None:
    client, _ = session_pair

    await client.close()
    await client.close()

    assert client.closed


@pytest.mark.asyncio
async def test_repr_contains_id(
    session_pair: tuple[ClientSession, ClientSession],
) -> None:
    client, _ = session_pair

    text = repr(client)

    assert "ClientSession" in text
    assert str(client.id) in text
