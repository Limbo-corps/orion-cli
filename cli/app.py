import typer

from cli.commands.voice import voice
from cli.commands.chat import chat
from cli.commands.doctor import doctor

app = typer.Typer(
    name="orion",
    help="Voice-Native AI Assistant",
)

app.command()(voice)
app.command()(chat)
app.command()(doctor)

if __name__ == "__main__":
    app()
