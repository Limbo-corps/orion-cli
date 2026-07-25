import asyncio

import typer

from orion.runtime.run import run

app = typer.Typer(
    name="orion",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main() -> None:
    asyncio.run(run())
