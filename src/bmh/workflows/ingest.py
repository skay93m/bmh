from __future__ import annotations

import textwrap
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.rule import Rule

from bmh.core.client import BMClient, BMError
from bmh.core.models import NoteTemplate, extract_task_items
from bmh.ui.cards import render_note_cards, render_note_card
from bmh.ui.banner import render_banner as _render_banner

console = Console()

# ── Canonical Note Templates ──────────────────────────────────────────────────

TEMPLATES: list[NoteTemplate] = [
    NoteTemplate(
        name="Task",
        folder="tasks",
        note_type="task",
        description="Active work item with checklist steps and status tracking.",
        default_tags=["task"],
    ),
    NoteTemplate(
        name="Insight / Learning",
        folder="insights",
        note_type="insight",
        description="Durable observation, learning, or derived knowledge.",
        default_tags=["insight"],
    ),
    NoteTemplate(
        name="Meeting / Sync",
        folder="meetings",
        note_type="meeting",
        description="Meeting record with participants, agenda, and action items.",
        default_tags=["meeting"],
    ),
    NoteTemplate(
        name="Decision Record",
        folder="decisions",
        note_type="decision",
        description="Architectural or operational decision with context and rationale.",
        default_tags=["decision"],
    ),
    NoteTemplate(
        name="Scratchpad / Freeform",
        folder="notes",
        note_type="note",
        description="General-purpose freeform note.",
        default_tags=[],
    ),
]


def _build_task_content(title: str, project: Optional[str]) -> str:
    """Interactively collect Task note fields."""
    console.print("[dim]Enter task details (press Enter to skip optional fields).[/dim]")
    assignee = Prompt.ask("  Assigned to", default="").strip()
    priority = Prompt.ask("  Priority (high/medium/low)", choices=["high", "medium", "low", ""], default="medium", show_choices=False).strip()
    steps_raw = Prompt.ask("  Checklist steps (comma-separated, e.g. 'Research, Draft, Review')", default="").strip()
    context = Prompt.ask("  Context or description (one line)", default="").strip()
    relations = Prompt.ask("  Relations (e.g. [[Note Title]], comma-separated; optional)", default="").strip()

    steps_md = ""
    if steps_raw:
        steps_list = [s.strip() for s in steps_raw.split(",") if s.strip()]
        steps_md = "\n".join(f"- [ ] {s}" for s in steps_list)

    relations_md = ""
    if relations:
        rel_list = [r.strip() for r in relations.split(",") if r.strip()]
        relations_md = "\n\n## Relations\n" + "\n".join(f"- [[{r.strip('[]')}]]" for r in rel_list)

    observations_block = "## Observations\n"
    if assignee:
        observations_block += f"- [assigned_to] {assignee}\n"
    if priority:
        observations_block += f"- [priority] {priority}\n"
    observations_block += "- [status] active\n"
    if context:
        observations_block += f"- [description] {context}\n"

    content = f"# {title}\n\n{observations_block}"
    if steps_md:
        content += f"\n## Steps\n{steps_md}\n"
    content += relations_md
    return content


def _build_insight_content(title: str, project: Optional[str]) -> str:
    """Interactively collect Insight note fields."""
    console.print("[dim]Enter insight details.[/dim]")
    summary = Prompt.ask("  One-line summary / core concept", default="").strip()
    key_insight = Prompt.ask("  Key insight or finding (one sentence)", default="").strip()
    references = Prompt.ask("  Source or reference link (optional)", default="").strip()

    content = f"# {title}\n\n## Summary\n{summary or '(No summary)'}\n\n## Key Insight\n"
    if key_insight:
        content += f"- [insight] {key_insight}\n"
    if references:
        content += f"\n## References\n- {references}\n"
    return content


def _build_meeting_content(title: str, project: Optional[str]) -> str:
    """Interactively collect Meeting note fields."""
    console.print("[dim]Enter meeting details.[/dim]")
    from datetime import date
    date_str = Prompt.ask("  Meeting date (YYYY-MM-DD)", default=str(date.today())).strip()
    participants = Prompt.ask("  Participants (comma-separated)", default="").strip()
    agenda = Prompt.ask("  Agenda items (comma-separated)", default="").strip()
    decisions = Prompt.ask("  Decisions made (comma-separated; optional)", default="").strip()
    action_items = Prompt.ask("  Action items (comma-separated; optional)", default="").strip()

    participants_md = "\n".join(f"- {p.strip()}" for p in participants.split(",") if p.strip()) if participants else "(None)"
    agenda_md = "\n".join(f"- {a.strip()}" for a in agenda.split(",") if a.strip()) if agenda else "(None)"

    content = f"# {title}\n\n## Observations\n- [date] {date_str}\n- [status] completed\n\n"
    content += f"## Participants\n{participants_md}\n\n"
    content += f"## Agenda\n{agenda_md}\n"
    if decisions:
        d_list = [d.strip() for d in decisions.split(",") if d.strip()]
        content += "\n## Decisions\n" + "\n".join(f"- [decision] {d}" for d in d_list) + "\n"
    if action_items:
        a_list = [a.strip() for a in action_items.split(",") if a.strip()]
        content += "\n## Action Items\n" + "\n".join(f"- [ ] {a}" for a in a_list) + "\n"
    return content


def _build_decision_content(title: str, project: Optional[str]) -> str:
    """Interactively collect Decision Record fields."""
    console.print("[dim]Enter decision record details.[/dim]")
    context = Prompt.ask("  Context / problem statement", default="").strip()
    options = Prompt.ask("  Options considered (comma-separated)", default="").strip()
    chosen = Prompt.ask("  Chosen option", default="").strip()
    rationale = Prompt.ask("  Rationale / reasoning", default="").strip()
    consequences = Prompt.ask("  Consequences / tradeoffs (optional)", default="").strip()

    options_md = "\n".join(f"- {o.strip()}" for o in options.split(",") if o.strip()) if options else "(None)"

    content = f"# {title}\n\n## Context\n{context or '(No context provided)'}\n\n"
    content += f"## Options Considered\n{options_md}\n\n"
    content += f"## Decision\n- [decision] {chosen or '(No decision recorded)'}\n\n"
    if rationale:
        content += f"## Rationale\n{rationale}\n"
    if consequences:
        content += f"\n## Consequences\n- [risk] {consequences}\n"
    return content


def _build_scratchpad_content(title: str, project: Optional[str]) -> str:
    """Interactively collect scratchpad / freeform content."""
    console.print("[dim]Enter note content (one line; use \\\\n for newlines).[/dim]")
    raw = Prompt.ask("  Content", default="").strip()
    body = raw.replace("\\n", "\n")
    return f"# {title}\n\n{body or '(No content)'}\n"


_TEMPLATE_BUILDERS = {
    "task": _build_task_content,
    "insight": _build_insight_content,
    "meeting": _build_meeting_content,
    "decision": _build_decision_content,
    "note": _build_scratchpad_content,
}


def flow_capture_wizard(client: BMClient) -> None:
    """Interactive Note Capture Wizard with structured templates."""
    console.print("\n[bold cyan]── 📝 Note Capture Wizard ──[/bold cyan]")
    console.print("[dim]Choose a template to get started:[/dim]\n")

    for i, tmpl in enumerate(TEMPLATES, start=1):
        console.print(f"  [bold cyan][{i}][/bold cyan] {tmpl.name}  [dim]— {tmpl.description}[/dim]")

    choice = Prompt.ask(
        "\nSelect template",
        choices=[str(i) for i in range(1, len(TEMPLATES) + 1)],
        default="1",
    ).strip()
    template = TEMPLATES[int(choice) - 1]

    console.print(f"\n[bold]Creating a [cyan]{template.name}[/cyan] note[/bold]")
    title = Prompt.ask("  Note title").strip()
    if not title:
        console.print("[yellow]Title cannot be empty. Returning to menu.[/yellow]")
        return

    project = Prompt.ask("  Project ('kancil', 'kensho', or leave empty for default)", default="").strip()
    folder = Prompt.ask(f"  Folder", default=template.folder).strip()
    tags_raw = Prompt.ask("  Tags (comma-separated; optional)", default=",".join(template.default_tags)).strip()

    builder = _TEMPLATE_BUILDERS.get(template.note_type, _build_scratchpad_content)
    content = builder(title, project)

    console.print("\n[bold]Preview:[/bold]")
    console.print(Rule(style="dim"))
    console.print(content)
    console.print(Rule(style="dim"))

    if not Confirm.ask("Create this note?", default=True):
        console.print("[dim]Note creation cancelled.[/dim]")
        return

    try:
        result = client.write_note(
            title=title,
            folder=folder,
            content=content,
            tags=tags_raw or None,
            note_type=template.note_type,
            project=project or None,
        )
        permalink = result.get("permalink") or result.get("entity") or result.get("file_path") or title
        console.print(f"\n[bold green]✅ Note created successfully![/bold green]")
        console.print(f"[dim]Permalink:[/dim] [cyan]{permalink}[/cyan]\n")
    except BMError as e:
        console.print(f"\n[bold red]Error creating note:[/bold red] {e}\n")


def flow_observation_appender(client: BMClient) -> None:
    """Quick Observation Appender: search and append to an existing note."""
    console.print("\n[bold cyan]── 🔖 Quick Observation Appender ──[/bold cyan]")
    query = Prompt.ask("  Search for note to append to").strip()
    if not query:
        console.print("[yellow]No query entered. Returning to menu.[/yellow]")
        return

    project = Prompt.ask("  Project filter (optional)", default="").strip()
    try:
        notes = client.search_notes(query=query, project=project or None)
    except BMError as e:
        console.print(f"[bold red]Search failed:[/bold red] {e}")
        return

    if not notes:
        console.print("[yellow]No matching notes found.[/yellow]")
        return

    console.print()
    for i, n in enumerate(notes[:10], start=1):
        entity = n.entity or n.permalink or n.file_path or "?"
        console.print(f"  [bold cyan][{i}][/bold cyan] {n.title}  [dim]{entity}[/dim]")

    choice = Prompt.ask("Select note", choices=[str(i) for i in range(1, min(len(notes), 10) + 1)], default="1")
    note = notes[int(choice) - 1]
    identifier = note.permalink or note.entity or note.file_path or note.title

    console.print(f"\n[bold]Appending observation to:[/bold] [cyan]{note.title}[/cyan]")

    tag_choices = ["decision", "insight", "risk", "todo", "status"]
    for i, t in enumerate(tag_choices, start=1):
        console.print(f"  [bold cyan][{i}][/bold cyan] [{t}]")

    tag_choice = Prompt.ask("Select observation tag", choices=[str(i) for i in range(1, len(tag_choices) + 1)], default="1")
    tag = tag_choices[int(tag_choice) - 1]
    observation_text = Prompt.ask(f"  Observation text").strip()

    if not observation_text:
        console.print("[yellow]Empty observation — aborting.[/yellow]")
        return

    observation_line = f"\n- [{tag}] {observation_text}"

    try:
        client.edit_note(
            identifier=str(identifier),
            operation="append",
            content=observation_line,
            project=project or None,
        )
        console.print(f"\n[bold green]✅ Observation appended successfully![/bold green]\n")
    except BMError as e:
        console.print(f"\n[bold red]Error appending observation:[/bold red] {e}\n")


def flow_piped_capture(client: BMClient, stdin_data: str) -> None:
    """Capture piped stdin as a new note."""
    console.print("\n[bold cyan]── 📥 Piped Note Capture ──[/bold cyan]")
    console.print(f"[dim]Received {len(stdin_data)} characters of piped input.[/dim]\n")

    title = Prompt.ask("  Note title for captured content").strip()
    if not title:
        console.print("[yellow]Title is required. Aborting piped capture.[/yellow]")
        return

    folder = Prompt.ask("  Folder", default="notes").strip()
    project = Prompt.ask("  Project (optional)", default="").strip()

    content = f"# {title}\n\n{stdin_data}"

    try:
        result = client.write_note(
            title=title,
            folder=folder,
            content=content,
            project=project or None,
        )
        permalink = result.get("permalink") or title
        console.print(f"[bold green]✅ Piped content saved as:[/bold green] [cyan]{permalink}[/cyan]\n")
    except BMError as e:
        console.print(f"[bold red]Error saving piped note:[/bold red] {e}\n")


def run_ingest_hub(client: Optional[BMClient] = None) -> None:
    """Top-level Ingest Hub interactive menu."""
    bm_client = client or BMClient()

    while True:
        console.print("\n[bold cyan]── 📥 Ingest Hub ──[/bold cyan]")
        console.print("  [bold cyan][1][/bold cyan] 📝 Note Capture Wizard  [dim](structured templates)[/dim]")
        console.print("  [bold cyan][2][/bold cyan] 🔖 Quick Observation Appender  [dim](append to existing note)[/dim]")
        console.print("  [bold cyan][0][/bold cyan] ↩  Back to Main Menu")
        console.print("[dim]──────────────────────────────────────────────[/dim]")

        try:
            choice = Prompt.ask(
                "Select action",
                choices=["1", "2", "0"],
                default="1",
                show_choices=False,
            ).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            flow_capture_wizard(bm_client)
        elif choice == "2":
            flow_observation_appender(bm_client)
        elif choice == "0":
            break

        if choice in ("1", "2"):
            try:
                cont = Prompt.ask("\n  Continue in Ingest Hub? (Enter or 'q' to go back)", default="")
                if cont.strip().lower() in ("q", "quit", "exit", "n", "no"):
                    break
            except (KeyboardInterrupt, EOFError):
                break
