from __future__ import annotations

import sys
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt

from bmh.core.client import BMClient, BMError, BMNotFoundError
from bmh.ui.banner import render_banner
from bmh.ui.cards import render_note_cards
from bmh.workflows.ingest import run_ingest_hub
from bmh.workflows.query import run_query_hub
from bmh.workflows.lint import run_lint_hub
from bmh.updater.engine import run_self_update

console = Console()


def _handle_client_error(e: Exception) -> None:
    """Display user-friendly error panels for BM errors."""
    if isinstance(e, BMNotFoundError):
        console.print(
            "\n[bold red]Error: Basic Memory CLI ('bm') not found.[/bold red]\n"
            "[yellow]Please make sure 'bm' is installed and available in your PATH.[/yellow]\n"
            "[dim]Refer to Basic Memory documentation for installation details.[/dim]\n"
        )
    elif isinstance(e, BMError):
        console.print(f"\n[bold red]Basic Memory Error:[/bold red] {e}\n")
    else:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}\n")



def run_interactive_session(client: Optional[BMClient] = None) -> None:
    """Main Tri-Modal interactive terminal session loop."""
    bm_client = client or BMClient()
    render_banner()


    while True:
        console.print("\n[bold]Select an operational mode:[/bold]")
        console.print("  [bold cyan][1][/bold cyan] 📥 Ingest   [dim]— Capture notes, structured templates & observation appender[/dim]")
        console.print("  [bold cyan][2][/bold cyan] 🔍 Query    [dim]— Search, active tasks, project browse & Guided Query Co-Pilot[/dim]")
        console.print("  [bold cyan][3][/bold cyan] 🩺 Lint     [dim]— Schema validation, orphan links & knowledge health checkup[/dim]")
        console.print("  [bold cyan][4][/bold cyan] 🔄 Update   [dim]— Pull and apply latest updates[/dim]")
        console.print("  [bold cyan][0][/bold cyan] 🚪 Exit")
        console.print("[dim]──────────────────────────────────────────────[/dim]")

        try:
            choice = Prompt.ask(
                "Select mode",
                choices=["1", "2", "3", "4", "0", "ingest", "query", "lint", "update", "exit", "q", "quit"],
                default="2",
                show_choices=False,
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]\n")
            break

        if choice in ("1", "ingest"):
            run_ingest_hub(bm_client)
        elif choice in ("2", "query"):
            run_query_hub(bm_client)
        elif choice in ("3", "lint"):
            run_lint_hub(bm_client)
        elif choice in ("4", "update"):
            run_self_update()
        elif choice in ("0", "exit", "q", "quit"):
            console.print("\n[dim]Goodbye![/dim]\n")
            break


# ── Backward-compatibility aliases ────────────────────────────────────────────
# These names were used in the original pre-Tri-Modal menu.py.
# They are preserved here so existing test code that imports from bmh.ui.menu
# continues to work without modification.

from bmh.workflows.query import (
    flow_keyword_search as flow_search_notes,
    flow_active_tasks,
    flow_project_browser as flow_browse_project,
    flow_recent_notes,
    flow_note_reader,
    flow_guided_query_copilot,
)

__all__ = [
    "_handle_client_error",
    "run_interactive_session",
    "run_ingest_hub",
    "run_query_hub",
    "run_lint_hub",
    "run_self_update",
    # Compat aliases
    "flow_search_notes",
    "flow_active_tasks",
    "flow_browse_project",
    "flow_recent_notes",
    "flow_note_reader",
    "flow_guided_query_copilot",
]
