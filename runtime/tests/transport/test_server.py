from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from orion.transport.server import IPCServer
from orion.transport.session import ClientSession


@pytest.mark.asyncio
async def test_server_startup_creates_socket(tmp_path: Path) -> None:
    socket_path = tmp_path / "orion.sock"

    async def handler(_: ClientSession) -> None:
        pass

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    assert not server.is_running

    await server.startup()

    assert server.is_running
    assert socket_path.exists()

    await server.shutdown()


@pytest.mark.asyncio
async def test_server_shutdown_removes_socket(tmp_path: Path) -> None:
    socket_path = tmp_path / "orion.sock"

    async def handler(_: ClientSession) -> None:
        pass

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    await server.startup()

    assert socket_path.exists()

    await server.shutdown()

    assert not server.is_running
    assert not socket_path.exists()


@pytest.mark.asyncio
async def test_accept_client_calls_session_handler(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "orion.sock"

    called = asyncio.Event()

    async def handler(session: ClientSession) -> None:
        assert isinstance(session, ClientSession)
        called.set()

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    await server.startup()

    _, writer = await asyncio.open_unix_connection(str(socket_path))

    await asyncio.wait_for(called.wait(), timeout=1)

    writer.close()
    await writer.wait_closed()

    await server.shutdown()


@pytest.mark.asyncio
async def test_multiple_clients(tmp_path: Path) -> None:
    socket_path = tmp_path / "orion.sock"

    count = 0

    async def handler(_: ClientSession) -> None:
        nonlocal count
        count += 1

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    await server.startup()

    clients = []

    for _ in range(3):
        _, writer = await asyncio.open_unix_connection(str(socket_path))
        clients.append(writer)

    await asyncio.sleep(0.1)

    assert count == 3

    for writer in clients:
        writer.close()
        await writer.wait_closed()

    await server.shutdown()


@pytest.mark.asyncio
async def test_shutdown_before_startup_is_safe(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "orion.sock"

    async def handler(_: ClientSession) -> None:
        pass

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    await server.shutdown()


@pytest.mark.asyncio
async def test_serve_forever_before_startup_raises(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "orion.sock"

    async def handler(_: ClientSession) -> None:
        pass

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    with pytest.raises(RuntimeError, match="has not been started"):
        await server.serve_forever()


@pytest.mark.asyncio
async def test_existing_socket_is_replaced(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "orion.sock"

    socket_path.touch()

    async def handler(_: ClientSession) -> None:
        pass

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    await server.startup()

    assert socket_path.exists()

    await server.shutdown()


@pytest.mark.asyncio
async def test_session_closed_after_handler_returns(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "orion.sock"

    session: ClientSession | None = None

    async def handler(client: ClientSession) -> None:
        nonlocal session
        session = client

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    await server.startup()

    _, writer = await asyncio.open_unix_connection(str(socket_path))

    await asyncio.sleep(0.1)

    assert session is not None
    assert session.closed

    writer.close()
    await writer.wait_closed()

    await server.shutdown()


@pytest.mark.asyncio
async def test_double_startup_raises(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "orion.sock"

    async def handler(_: ClientSession) -> None:
        pass

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    await server.startup()

    with pytest.raises(RuntimeError, match="already running"):
        await server.startup()

    await server.shutdown()


@pytest.mark.asyncio
async def test_can_restart_after_shutdown(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "orion.sock"

    async def handler(_: ClientSession) -> None:
        pass

    server = IPCServer(
        socket_path=socket_path,
        session_handler=handler,
    )

    await server.startup()
    await server.shutdown()

    assert not server.is_running

    await server.startup()

    assert server.is_running
    assert socket_path.exists()

    await server.shutdown()
