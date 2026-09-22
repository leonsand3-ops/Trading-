"""Command line entry point."""

import typer

from swing import __version__

app = typer.Typer(no_args_is_help=True, help="Beslutsstöd för swing trading.")


@app.callback()
def main() -> None:
    """Swing trading decision support."""


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(__version__)
