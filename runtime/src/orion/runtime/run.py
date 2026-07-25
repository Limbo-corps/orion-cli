"""
Application entrypoint.

Constructs the Orion runtime, registers long-lived components,
starts the application, and performs graceful shutdown.
"""

from __future__ import annotations


from dotenv import load_dotenv
from langchain_groq import ChatGroq
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orion.bus.event_bus import EventBus
from orion.memory.config import MemoryConfig
from orion.memory.module import MemoryModule
from orion.memory.planner.planner import RetrievalPlanner
from orion.orchestrator.config import OrchestratorConfig
from orion.orchestrator.orchestrator import Orchestrator
from orion.runtime.runtime import OrionRuntime
from orion.store.sqlite_store import SQLiteEventStore
from orion.transport.bridge import IPCBridge
from orion.transport.server import IPCServer

console = Console()


def create_llm() -> ChatGroq:
    """Create the application's primary LLM."""

    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
    )


def print_startup_banner() -> None:
    """Display Orion startup information."""

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", justify="right")
    table.add_column()

    table.add_row("Status", "[bold green]READY[/]")
    table.add_row("Memory", "Initialized")
    table.add_row("Event Store", "Connected")
    table.add_row("Orchestrator", "Running")

    console.print()
    console.print(
        Panel(
            table,
            title="[bold blue]ORION[/]",
            subtitle="[green]Orchestration Assistant[/]",
            border_style="blue",
        )
    )
    console.print("[bold green]✓ Orion started successfully.[/]")
    console.print("[dim]Waiting for incoming requests...[/]")
    console.print()


async def run() -> None:
    """Run the Orion application."""

    load_dotenv()

    runtime = OrionRuntime()

    llm = create_llm()

    store = SQLiteEventStore()
    bus = EventBus(store)

    memory = MemoryModule(
        config=MemoryConfig(),
        planner=RetrievalPlanner(llm=llm),
    )

    bridge = IPCBridge(bus)

    orchestrator = Orchestrator(
        bus=bus,
        config=OrchestratorConfig(
            llm=llm,
            memory=memory,
            bridge=bridge,
        ),
    )

    server = IPCServer(
        socket_path="/tmp/orion.sock",
        session_handler=bridge.serve,
    )

    runtime.register(store)
    runtime.register(memory)
    runtime.register(orchestrator)
    runtime.register(server)

    await runtime.startup()

    print_startup_banner()

    try:
        await server.serve_forever()
    finally:
        console.print()
        console.print("[yellow]Shutting down Orion...[/]")
        await runtime.shutdown()
        console.print("[green]Shutdown complete.[/]")
