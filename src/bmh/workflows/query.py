from __future__ import annotations

from typing import List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.text import Text

from bmh.core.client import BMClient, BMError
from bmh.core.models import NoteModel, extract_task_items
from bmh.ui.cards import render_note_cards, render_note_card

console = Console()

# ── Project constants ─────────────────────────────────────────────────────────
KNOWN_PROJECTS = ["kancil", "kensho"]


def _handle_error(e: Exception) -> None:
    if isinstance(e, BMError):
        console.print(f"\n[bold red]Basic Memory Error:[/bold red] {e}\n")
    else:
        console.print(f"\n[bold red]Error:[/bold red] {e}\n")


# ── Core Search Flows ─────────────────────────────────────────────────────────

def flow_keyword_search(client: BMClient) -> None:
    """Interactive keyword/title search."""
    console.print("\n[bold cyan]── 🔍 Search Notes ──[/bold cyan]")
    query = Prompt.ask("  Enter search query").strip()
    if not query:
        console.print("[yellow]No query entered.[/yellow]")
        return

    is_title = Confirm.ask("  Search in titles only?", default=False)
    project = Prompt.ask("  Project filter (kancil/kensho/empty)", default="").strip()

    console.print("\n[dim]Searching...[/dim]")
    try:
        notes = client.search_notes(query=query, project=project or None, is_title=is_title)
        render_note_cards(notes)
    except Exception as e:
        _handle_error(e)


def flow_active_tasks(client: BMClient) -> None:
    """View active tasks with optional step checkoff."""
    console.print("\n[bold yellow]── ⚡ Active Tasks ──[/bold yellow]")
    project = Prompt.ask("  Project filter (kancil/kensho/empty)", default="").strip()

    console.print("\n[dim]Fetching active tasks...[/dim]")
    try:
        notes = client.search_notes(query=None, project=project or None, note_type="task", status="active")
    except Exception as e:
        _handle_error(e)
        return

    if not notes:
        console.print("[yellow]No active tasks found.[/yellow]")
        return

    render_note_cards(notes)

    if not Confirm.ask("\n  Inspect a task's steps?", default=False):
        return

    choices = [str(i) for i in range(1, min(len(notes), 10) + 1)]
    for i, n in enumerate(notes[:10], start=1):
        console.print(f"  [{i}] {n.title}")

    choice = Prompt.ask("  Select task", choices=choices, default="1")
    note = notes[int(choice) - 1]

    steps = extract_task_items(note.content)
    if not steps:
        console.print("[dim]No checklist steps found in this task.[/dim]")
        return

    console.print(f"\n[bold]Steps for:[/bold] [cyan]{note.title}[/cyan]")
    for s in steps:
        icon = "[green]☑[/green]" if s.completed else "[dim]☐[/dim]"
        console.print(f"  {icon} [{s.index}] {s.text}")

    if not Confirm.ask("\n  Check off a step?", default=False):
        return

    step_choices = [str(s.index) for s in steps if not s.completed]
    if not step_choices:
        console.print("[green]All steps already completed![/green]")
        return

    step_idx = Prompt.ask("  Enter step number to mark done", choices=step_choices)
    step = next(s for s in steps if str(s.index) == step_idx)
    identifier = note.permalink or note.entity or note.file_path or note.title

    try:
        client.edit_note(
            identifier=str(identifier),
            operation="find_replace",
            content=step.raw_line.replace("[ ]", "[x]", 1),
            find_text=step.raw_line,
            project=project or None,
        )
        console.print(f"[bold green]✅ Step {step.index} marked complete![/bold green]")
    except BMError as e:
        console.print(f"[bold red]Error checking off step:[/bold red] {e}")


def flow_project_browser(client: BMClient) -> None:
    """Browse notes by project."""
    console.print("\n[bold blue]── 📚 Browse by Project ──[/bold blue]")
    for i, p in enumerate(KNOWN_PROJECTS, start=1):
        console.print(f"  [bold cyan][{i}][/bold cyan] {p}")

    choice = Prompt.ask("  Select project", choices=[str(i) for i in range(1, len(KNOWN_PROJECTS) + 1)], default="1")
    project = KNOWN_PROJECTS[int(choice) - 1]
    query = Prompt.ask(f"  Search query within [cyan]{project}[/cyan] (optional)", default="").strip()

    console.print(f"\n[dim]Browsing '{project}'...[/dim]")
    try:
        notes = client.search_notes(query=query or None, project=project)
        render_note_cards(notes)
    except Exception as e:
        _handle_error(e)


def flow_recent_notes(client: BMClient) -> None:
    """View recent notes across the knowledge base."""
    console.print("\n[bold magenta]── 🕒 Recent Notes ──[/bold magenta]")
    project = Prompt.ask("  Project filter (kancil/kensho/empty)", default="").strip()
    page_size = Prompt.ask("  Number of results", default="10").strip()

    console.print("\n[dim]Fetching recent activity...[/dim]")
    try:
        activity = client.recent_activity(project=project or None, page_size=int(page_size))
    except Exception as e:
        _handle_error(e)
        return

    if not activity:
        console.print("[yellow]No recent activity found.[/yellow]")
        return

    notes: List[NoteModel] = []
    for item in activity:
        if isinstance(item, dict):
            from bmh.core.models import _dict_to_note
            notes.append(_dict_to_note(item))
        elif isinstance(item, NoteModel):
            notes.append(item)

    render_note_cards(notes)


def flow_note_reader(client: BMClient) -> None:
    """Read a single note in full detail."""
    console.print("\n[bold cyan]── 📖 Note Detail Reader ──[/bold cyan]")
    identifier = Prompt.ask("  Enter note permalink or title").strip()
    if not identifier:
        console.print("[yellow]No identifier provided.[/yellow]")
        return

    project = Prompt.ask("  Project (optional)", default="").strip()

    console.print("\n[dim]Reading note...[/dim]")
    try:
        data = client.read_note(identifier=identifier, project=project or None)
    except BMError as e:
        _handle_error(e)
        return

    if not data:
        console.print(f"[yellow]Note not found: '{identifier}'[/yellow]")
        return

    from bmh.core.models import _dict_to_note
    note = _dict_to_note(data)
    panel = render_note_card(note, index=1, total=1)
    console.print(panel)


# ── Guided Query Co-Pilot ─────────────────────────────────────────────────────

def flow_guided_query_copilot(client: BMClient) -> None:
    """Guided Query Co-Pilot — /grill-me style query formulator."""
    console.print("\n[bold cyan]── 🧭 Guided Query Co-Pilot ──[/bold cyan]")
    console.print("[dim]I'll help you formulate the best possible query step by step.[/dim]\n")

    # Step 1: Intent
    intent = Prompt.ask("  What are you looking for? (describe in your own words)").strip()
    if not intent:
        console.print("[yellow]No intent described. Returning to menu.[/yellow]")
        return

    # Step 2: Narrow by note type
    console.print("\n  What kind of note are you looking for?")
    console.print("  [dim][1] Any type  [2] Task  [3] Insight/Decision  [4] Meeting  [5] Note/Scratchpad[/dim]")
    type_choice = Prompt.ask("  Type", choices=["1", "2", "3", "4", "5"], default="1").strip()
    type_map = {"1": None, "2": "task", "3": "insight", "4": "meeting", "5": "note"}
    note_type = type_map[type_choice]

    # Step 3: Project scope
    console.print("\n  [dim][1] All projects  [2] kancil  [3] kensho[/dim]")
    proj_choice = Prompt.ask("  Project scope", choices=["1", "2", "3"], default="1").strip()
    proj_map = {"1": None, "2": "kancil", "3": "kensho"}
    project = proj_map[proj_choice]

    # Step 4: Time range
    console.print("\n  Any date constraint?")
    console.print("  [dim][1] No constraint  [2] Last 7 days  [3] Last 30 days  [4] Last 90 days[/dim]")
    date_choice = Prompt.ask("  Date range", choices=["1", "2", "3", "4"], default="1").strip()
    date_map = {"1": None, "2": "7d", "3": "30d", "4": "90d"}
    after_date = date_map[date_choice]

    # Step 5: Search mode
    title_only = Confirm.ask("\n  Search in note titles only? (No for full-text)", default=False)

    # Step 6: Status (for tasks)
    status: Optional[str] = None
    if note_type == "task":
        console.print("\n  Task status filter:")
        console.print("  [dim][1] Any status  [2] Active only  [3] Completed only[/dim]")
        st_choice = Prompt.ask("  Status", choices=["1", "2", "3"], default="1").strip()
        status_map = {"1": None, "2": "active", "3": "done"}
        status = status_map[st_choice]

    # Show formulated query summary
    console.print("\n[bold]Formulated Search:[/bold]")
    console.print(f"  Query: [cyan]{intent}[/cyan]")
    console.print(f"  Type: [cyan]{note_type or 'any'}[/cyan]")
    console.print(f"  Project: [cyan]{project or 'all'}[/cyan]")
    console.print(f"  After date: [cyan]{after_date or 'any'}[/cyan]")
    console.print(f"  Title only: [cyan]{title_only}[/cyan]")
    if status:
        console.print(f"  Status: [cyan]{status}[/cyan]")

    if not Confirm.ask("\n  Execute this search?", default=True):
        console.print("[dim]Search cancelled.[/dim]")
        return

    console.print("\n[dim]Searching...[/dim]")
    try:
        notes = client.search_notes(
            query=intent,
            project=project,
            note_type=note_type,
            status=status,
            is_title=title_only,
            after_date=after_date,
        )
        render_note_cards(notes)
    except Exception as e:
        _handle_error(e)


# ── Query Hub Runner ──────────────────────────────────────────────────────────

def run_query_hub(client: Optional[BMClient] = None) -> None:
    """Top-level Query Hub interactive menu."""
    bm_client = client or BMClient()

    while True:
        console.print("\n[bold cyan]── 🔍 Query Hub ──[/bold cyan]")
        console.print("  [bold cyan][1][/bold cyan] 🔍 Search Notes  [dim](keyword/title)[/dim]")
        console.print("  [bold cyan][2][/bold cyan] ⚡ Active Tasks  [dim](tasks + step checkoff)[/dim]")
        console.print("  [bold cyan][3][/bold cyan] 📚 Browse by Project  [dim](kancil / kensho)[/dim]")
        console.print("  [bold cyan][4][/bold cyan] 🕒 Recent Notes")
        console.print("  [bold cyan][5][/bold cyan] 📖 Note Detail Reader")
        console.print("  [bold cyan][6][/bold cyan] 🧭 Guided Query Co-Pilot  [dim](formulate the perfect query)[/dim]")
        console.print("  [bold cyan][0][/bold cyan] ↩  Back to Main Menu")
        console.print("[dim]──────────────────────────────────────────────[/dim]")

        try:
            choice = Prompt.ask(
                "Select action",
                choices=["1", "2", "3", "4", "5", "6", "0"],
                default="1",
                show_choices=False,
            ).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            flow_keyword_search(bm_client)
        elif choice == "2":
            flow_active_tasks(bm_client)
        elif choice == "3":
            flow_project_browser(bm_client)
        elif choice == "4":
            flow_recent_notes(bm_client)
        elif choice == "5":
            flow_note_reader(bm_client)
        elif choice == "6":
            flow_guided_query_copilot(bm_client)
        elif choice == "0":
            break

        if choice not in ("0",):
            try:
                cont = Prompt.ask("\n  Continue in Query Hub? (Enter or 'q' to go back)", default="")
                if cont.strip().lower() in ("q", "quit", "exit", "n", "no"):
                    break
            except (KeyboardInterrupt, EOFError):
                break
