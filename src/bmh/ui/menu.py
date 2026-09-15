from __future__ import annotations

import sys
from typing import Optional
from rich.console import Console
from rich.prompt import Confirm, Prompt

from bmh.core.client import BMClient, BMError, BMNotFoundError
from bmh.ui.banner import render_banner
from bmh.ui.cards import render_note_cards

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


def flow_search_notes(client: BMClient) -> None:
    """Interactive flow: search notes by query, title, or project."""
    console.print("\n[bold cyan]── 🔍 Search Notes ──[/bold cyan]")
    query = Prompt.ask("Enter search query (or press Enter for all)", default="").strip()

    is_title = False
    if query:
        is_title = Confirm.ask("Search in title only?", default=False)

    project = Prompt.ask(
        "Project filter ('kancil', 'kensho', or leave empty for all)", default=""
    ).strip()

    console.print("\n[cyan]Searching Basic Memory...[/cyan]")
    try:
        notes = client.search_notes(
            query=query or None,
            project=project or None,
            is_title=is_title,
        )
        render_note_cards(notes)
    except Exception as e:
        _handle_client_error(e)


def flow_active_tasks(client: BMClient) -> None:
    """Interactive flow: discover active tasks."""
    console.print("\n[bold yellow]── ⚡ Active Tasks ──[/bold yellow]")
    project = Prompt.ask(
        "Project filter ('kancil', 'kensho', or leave empty for all)", default=""
    ).strip()

    console.print("\n[cyan]Retrieving active tasks...[/cyan]")
    try:
        notes = client.search_notes(
            query=None,
            project=project or None,
            note_type="task",
            status="active",
        )
        render_note_cards(notes)
    except Exception as e:
        _handle_client_error(e)


def flow_browse_project(client: BMClient) -> None:
    """Interactive flow: browse by project knowledge base."""
    console.print("\n[bold blue]── 📚 Browse by Project ──[/bold blue]")
    console.print("  [cyan][1][/cyan] kancil [dim](operational life & agent tasks)[/dim]")
    console.print("  [cyan][2][/cyan] kensho [dim](durable knowledge base)[/dim]")

    choice = Prompt.ask("Select project", choices=["1", "2", "kancil", "kensho"], default="1")
    project = "kensho" if choice in ("2", "kensho") else "kancil"

    query = Prompt.ask(f"Search query within [bold]{project}[/bold] (optional)", default="").strip()

    console.print(f"\n[cyan]Browsing project '{project}'...[/cyan]")
    try:
        notes = client.search_notes(
            query=query or None,
            project=project,
        )
        render_note_cards(notes)
    except Exception as e:
        _handle_client_error(e)


def flow_recent_notes(client: BMClient) -> None:
    """Interactive flow: view recent notes."""
    console.print("\n[bold magenta]── 🕒 Recent Notes ──[/bold magenta]")
    project = Prompt.ask(
        "Project filter ('kancil', 'kensho', or leave empty for all)", default=""
    ).strip()

    console.print("\n[cyan]Fetching recent notes...[/cyan]")
    try:
        notes = client.search_notes(
            query=None,
            project=project or None,
        )
        render_note_cards(notes)
    except Exception as e:
        _handle_client_error(e)


def run_interactive_session(client: Optional[BMClient] = None) -> None:
    """Main interactive terminal session loop."""
    bm_client = client or BMClient()
    render_banner()

    while True:
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("  [bold cyan][1][/bold cyan] 🔍 Search notes [dim](by title or content)[/dim]")
        console.print("  [bold cyan][2][/bold cyan] ⚡ View active tasks [dim](current commitments)[/dim]")
        console.print("  [bold cyan][3][/bold cyan] 📚 Browse by project [dim](kancil / kensho)[/dim]")
        console.print("  [bold cyan][4][/bold cyan] 🕒 View recent notes")
        console.print("  [bold cyan][5][/bold cyan] 🔄 Update bmh [dim](pull latest release)[/dim]")
        console.print("  [bold cyan][0][/bold cyan] 🚪 Exit")
        console.print("[dim]──────────────────────────────────────────────[/dim]")

        try:
            choice = Prompt.ask(
                "Select an option",
                choices=["1", "2", "3", "4", "5", "0", "search", "tasks", "task", "project", "recent", "update", "exit", "q", "quit"],
                default="1",
                show_choices=False,
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]\n")
            break

        if choice in ("1", "search"):
            flow_search_notes(bm_client)
        elif choice in ("2", "tasks", "task"):
            flow_active_tasks(bm_client)
        elif choice in ("3", "project"):
            flow_browse_project(bm_client)
        elif choice in ("4", "recent"):
            flow_recent_notes(bm_client)
        elif choice in ("5", "update"):
            from bmh.updater.engine import run_self_update
            run_self_update()
        elif choice in ("0", "exit", "q", "quit"):
            console.print("\n[dim]Goodbye![/dim]\n")
            break

        console.print("\n[dim]──────────────────────────────────────────────[/dim]")
        try:
            cont = Prompt.ask("Press Enter to return to main menu (or 'q' to quit)", default="")
            if cont.strip().lower() in ("q", "quit", "exit"):
                console.print("\n[dim]Goodbye![/dim]\n")
                break
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]\n")
            break
