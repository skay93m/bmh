from __future__ import annotations

import re
from typing import List, Optional
from rich.console import Console, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from bmh.core.models import NoteModel

console = Console()

# Observation tags and their corresponding Rich color styling
TAG_REPLACEMENTS = {
    re.compile(r"\[decision\]", re.IGNORECASE): "[bold green]\\[decision][/bold green]",
    re.compile(r"\[insight\]", re.IGNORECASE): "[bold magenta]\\[insight][/bold magenta]",
    re.compile(r"\[risk\]", re.IGNORECASE): "[bold red]\\[risk][/bold red]",
    re.compile(r"\[todo\]", re.IGNORECASE): "[bold yellow]\\[todo][/bold yellow]",
    re.compile(r"\[status\]", re.IGNORECASE): "[bold blue]\\[status][/bold blue]",
    re.compile(r"\[x\]", re.IGNORECASE): "[green]☑[/green]",
    re.compile(r"\[ \]", re.IGNORECASE): "[dim]☐[/dim]",
}


def _highlight_observations(content: str) -> str:
    """Format inline observation tags and checkboxes with rich markup."""
    highlighted = content
    for pattern, replacement in TAG_REPLACEMENTS.items():
        highlighted = pattern.sub(replacement, highlighted)
    return highlighted


def _format_date(date_str: Optional[str]) -> Optional[str]:
    """Format ISO timestamp to DD/MM/YY HH:MM format if applicable."""
    if not date_str:
        return None
    # Match YYYY-MM-DDTHH:MM or YYYY-MM-DD HH:MM
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?", date_str)
    if match:
        y, m, d, hh, mm = match.groups()
        short_year = y[2:]
        if hh and mm:
            return f"{d}/{m}/{short_year} {hh}:{mm}"
        return f"{d}/{m}/{short_year}"
    return date_str


def render_note_card(note: NoteModel, index: int = 1, total: int = 1) -> Panel:
    """Render a single NoteModel as a structured Rich Panel."""
    # Title header
    counter_str = f" [{index}/{total}]" if total > 1 else ""
    header_title = f"📌 {note.title}{counter_str}"

    # Body formatting
    content_body = note.content.strip() or "(No content)"
    body_renderable: RenderableType
    try:
        body_renderable = Markdown(content_body)
    except Exception:
        body_renderable = Text(content_body)

    # Footer metadata
    footer_elements: List[str] = []
    if note.entity:
        footer_elements.append(f"[bold cyan]entity:[/bold cyan] {note.entity}")
    if note.external_id:
        footer_elements.append(f"[bold cyan]external_id:[/bold cyan] {note.external_id}")
    if note.file_path and note.file_path != note.entity:
        footer_elements.append(f"[dim]file:[/dim] {note.file_path}")
    if note.updated_at:
        formatted_dt = _format_date(note.updated_at)
        if formatted_dt:
            footer_elements.append(f"[dim]updated:[/dim] {formatted_dt}")

    subtitle = " | ".join(footer_elements) if footer_elements else None

    return Panel(
        body_renderable,
        title=header_title,
        title_align="left",
        subtitle=subtitle,
        subtitle_align="left",
        border_style="cyan",
        padding=(1, 2),
    )


def render_note_cards(notes: List[NoteModel], custom_console: Optional[Console] = None) -> None:
    """Render a collection of NoteModel cards to the console."""
    target_console = custom_console or console

    if not notes:
        target_console.print("\n[yellow]No notes found matching criteria.[/yellow]\n")
        return

    target_console.print()
    total = len(notes)
    for idx, note in enumerate(notes, start=1):
        panel = render_note_card(note, index=idx, total=total)
        target_console.print(panel)
        target_console.print()
