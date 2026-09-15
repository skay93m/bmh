from __future__ import annotations

import sys
from typing import Optional
import typer
from rich.console import Console

import bmh
from bmh.core.models import normalize_notes_json
from bmh.ui.cards import render_note_cards
from bmh.ui.menu import run_interactive_session
from bmh.updater.engine import run_self_update

console = Console()

app = typer.Typer(
    no_args_is_help=False,
    add_completion=False,
    help="bmh - Purely interactive CLI companion and structured card inspector for Basic Memory (bm)",
)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"bmh version {bmh.__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """bmh is a purely interactive companion for Basic Memory (bm).

    It guides you through searching notes, discovering active tasks,
    and browsing projects, then renders every note in clean, structured cards.
    """
    if ctx.invoked_subcommand is not None:
        return

    # Check if stdin has piped data
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
        if input_data.strip():
            notes = normalize_notes_json(input_data)
            render_note_cards(notes)
        else:
            console.print("\n[yellow]No input provided on stdin.[/yellow]\n")
        return

    # Default interactive session for human developers
    run_interactive_session()


@app.command(name="update", help="Pull and apply the latest updates from GitHub.")
def update_cmd() -> None:
    """Pull and apply the latest updates from GitHub."""
    success = run_self_update()
    if not success:
        raise typer.Exit(code=1)


def cli_entrypoint() -> None:
    """Global script entry point for bmh."""
    try:
        app()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Interrupted. Exiting bmh.[/dim]\n")
        sys.exit(0)


if __name__ == "__main__":
    cli_entrypoint()
