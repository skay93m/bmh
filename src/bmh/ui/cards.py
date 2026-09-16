from __future__ import annotations

import re
from typing import Any, List, Optional
from pydantic import BaseModel
from rich import box
from rich.console import Console, Group, RenderableType
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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


def highlight_observations(content: Optional[str]) -> str:
    """Format inline observation tags and checkboxes with rich markup."""
    if not content:
        return ""
    highlighted = str(content)
    for pattern, replacement in TAG_REPLACEMENTS.items():
        highlighted = pattern.sub(replacement, highlighted)
    return highlighted


_highlight_observations = highlight_observations


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


def render_note_card(
    note: NoteModel,
    index: int = 1,
    total: int = 1,
    custom_console: Optional[Console] = None,
) -> Panel:
    """Render a single NoteModel as a structured Rich Panel with highlighted observation badges."""
    # Title header
    counter_str = f" [{index}/{total}]" if total > 1 else ""
    header_title = f"📌 {escape(note.title or 'Untitled Note')}{escape(counter_str)}"

    # Body formatting with observation highlights
    content_body = (note.content or "").strip() or "(No content)"
    highlighted_body = highlight_observations(content_body)

    body_renderable: RenderableType
    try:
        body_renderable = Text.from_markup(highlighted_body)
    except Exception:
        try:
            body_renderable = Markdown(content_body)
        except Exception:
            body_renderable = Text(content_body)

    # Footer metadata
    footer_elements: List[str] = []
    if note.entity:
        footer_elements.append(f"[bold cyan]entity:[/bold cyan] {escape(str(note.entity))}")
    if note.external_id:
        footer_elements.append(f"[bold cyan]external_id:[/bold cyan] {escape(str(note.external_id))}")
    if note.file_path and note.file_path != note.entity:
        footer_elements.append(f"[dim]file:[/dim] {escape(str(note.file_path))}")
    if note.updated_at:
        formatted_dt = _format_date(note.updated_at)
        if formatted_dt:
            footer_elements.append(f"[dim]updated:[/dim] {escape(str(formatted_dt))}")

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


def render_schema_validation_panel(data: Any) -> Panel:
    """Render schema validation report as a structured Rich Panel."""
    if isinstance(data, BaseModel):
        data = data.model_dump()
    elif not isinstance(data, dict):
        data = {}

    if data.get("error"):
        error_msg = data.get("error", "Unknown validation error")
        return Panel(
            Text(f"Error: {error_msg}", style="bold red"),
            title="[bold red]📐 Schema Validation Error[/bold red]",
            title_align="left",
            border_style="red",
            padding=(1, 2),
        )

    total = data.get("total_notes", 0)
    valid = data.get("valid_count", 0)
    warnings = data.get("warning_count", 0)
    errors = data.get("error_count", 0)

    summary = Text.from_markup(
        f"Total Notes: [bold]{total}[/bold] | "
        f"Valid: [bold green]{valid}[/bold green] | "
        f"Warnings: [bold yellow]{warnings}[/bold yellow] | "
        f"Errors: [bold red]{errors}[/bold red]\n"
    )

    results = data.get("results", [])
    if results:
        table = Table(box=box.ROUNDED, expand=True)
        table.add_column("Note / Identifier", style="bold cyan", ratio=3)
        table.add_column("Schema", style="magenta", ratio=2)
        table.add_column("Status", justify="center", ratio=1)
        table.add_column("Issues / Warnings", style="dim", ratio=4)

        for r in results:
            if isinstance(r, BaseModel):
                r = r.model_dump()
            elif not isinstance(r, dict):
                continue
            ident = escape(str(r.get("note_identifier", "Unknown")))
            schema = escape(str(r.get("schema_entity") or r.get("schema") or "None"))
            passed = r.get("passed", True)
            err_list = r.get("errors", [])
            warn_list = r.get("warnings", [])

            if err_list:
                status = "[bold red]FAIL[/bold red]"
                issues = escape("; ".join(str(e) for e in err_list))
            elif warn_list:
                status = "[bold yellow]WARN[/bold yellow]"
                issues = escape("; ".join(str(w) for w in warn_list))
            elif passed:
                status = "[bold green]PASS[/bold green]"
                issues = "All checks passed"
            else:
                status = "[bold red]FAIL[/bold red]"
                issues = "Schema check failed"
            table.add_row(ident, schema, status, issues)
        renderables = [summary, table]
    else:
        status_msg = Text.from_markup("[bold green]✓ All schemas valid with zero errors or warnings.[/bold green]")
        renderables = [summary, status_msg]

    border_color = "red" if errors > 0 else ("yellow" if warnings > 0 else "green")
    return Panel(
        Group(*renderables),
        title="📐 Schema Validation Report",
        title_align="left",
        border_style=border_color,
        padding=(1, 2),
    )


def render_orphan_list_panel(orphans: Any) -> Panel:
    """Render orphan entities table or clean confirmation."""
    if isinstance(orphans, dict):
        if "error" in orphans:
            msg = Text(f"Error: {orphans['error']}", style="bold red")
            return Panel(
                msg,
                title="[bold red]🔗 Orphan Link Error[/bold red]",
                title_align="left",
                border_style="red",
                padding=(1, 2),
            )
        orphans = [orphans]
    elif isinstance(orphans, BaseModel):
        orphans = [orphans.model_dump()]
    elif not isinstance(orphans, list):
        orphans = []

    if not orphans:
        msg = Text.from_markup(
            "[bold green]✨ Knowledge graph clean: No orphan entities found![/bold green]\n\n"
            "[dim]All notes are properly connected with incoming or outgoing relations.[/dim]"
        )
        return Panel(
            msg,
            title="🔗 Orphan Link Inspector",
            title_align="left",
            border_style="green",
            padding=(1, 2),
        )

    if len(orphans) == 1 and isinstance(orphans[0], dict) and "error" in orphans[0]:
        msg = Text(f"Error: {orphans[0]['error']}", style="bold red")
        return Panel(
            msg,
            title="[bold red]🔗 Orphan Link Error[/bold red]",
            title_align="left",
            border_style="red",
            padding=(1, 2),
        )

    table = Table(box=box.ROUNDED, expand=True)
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Title", style="bold cyan")
    table.add_column("Type", style="magenta")
    table.add_column("File Path", style="dim")
    table.add_column("External ID", style="dim")

    valid_count = 0
    for raw_item in orphans:
        if raw_item is None:
            continue
        if isinstance(raw_item, BaseModel):
            item = raw_item.model_dump()
        elif isinstance(raw_item, dict):
            item = raw_item
        elif isinstance(raw_item, str):
            item = {"title": raw_item}
        else:
            item = {"title": str(raw_item)}

        valid_count += 1
        table.add_row(
            str(valid_count),
            escape(str(item.get("title") or "Untitled")),
            escape(str(item.get("note_type") or item.get("type") or "note")),
            escape(str(item.get("file_path") or "")),
            escape(str(item.get("external_id") or "")),
        )

    if valid_count == 0:
        msg = Text.from_markup(
            "[bold green]✨ Knowledge graph clean: No orphan entities found![/bold green]\n\n"
            "[dim]All notes are properly connected with incoming or outgoing relations.[/dim]"
        )
        return Panel(
            msg,
            title="🔗 Orphan Link Inspector",
            title_align="left",
            border_style="green",
            padding=(1, 2),
        )

    footer = Text.from_markup(
        f"\n[dim]Found {valid_count} orphan entities with no relations in knowledge graph.[/dim]"
    )
    return Panel(
        Group(table, footer),
        title=f"🔗 Orphan Entities ({valid_count} found)",
        title_align="left",
        border_style="yellow",
        padding=(1, 2),
    )


def render_doctor_panel(data: Any) -> Panel:
    """Render bm doctor consistency check results."""
    if isinstance(data, BaseModel):
        data = data.model_dump()
    elif not isinstance(data, dict):
        data = {}

    passed = data.get("passed", False) or data.get("status") == "passed"
    output = data.get("output", "")
    steps = data.get("steps", [])

    elements = []
    if steps:
        step_text = Text()
        for s in steps:
            step_text.append("✓ ", style="bold green" if passed else "dim")
            step_text.append(f"{s}\n", style="white")
        elements.append(step_text)

    if passed:
        elements.append(
            Text.from_markup(
                "[bold green]🩺 Doctor Status: Healthy & Synced[/bold green]\n"
                "[dim]All file storage, indexer, and search clients verified.[/dim]"
            )
        )
        title = "🩺 Basic Memory Doctor (Passed)"
        border = "green"
    else:
        elements.append(
            Text.from_markup(
                f"[bold red]🩺 Doctor Status: Check Failed[/bold red]\n"
                f"[dim]{escape(str(output or 'Consistency check failed'))}[/dim]"
            )
        )
        title = "🩺 Basic Memory Doctor (Failed)"
        border = "red"

    return Panel(
        Group(*elements) if elements else Text(output or "Doctor completed."),
        title=title,
        title_align="left",
        border_style=border,
        padding=(1, 2),
    )


def render_schema_diff_panel(data: Any) -> Panel:
    """Render schema drift analysis."""
    if isinstance(data, BaseModel):
        data = data.model_dump()
    elif not isinstance(data, dict):
        data = {}

    if data.get("error"):
        return Panel(
            Text(f"Error: {data['error']}", style="bold red"),
            title="[bold red]📊 Schema Drift Analysis[/bold red]",
            title_align="left",
            border_style="red",
            padding=(1, 2),
        )

    note_type = data.get("note_type", "Unknown")
    schema_found = data.get("schema_found", True)

    if not schema_found:
        return Panel(
            Text.from_markup(f"[bold yellow]No schema definition found for note type '{escape(str(note_type))}'.[/bold yellow]"),
            title=f"📊 Schema Drift: {escape(str(note_type))}",
            title_align="left",
            border_style="yellow",
            padding=(1, 2),
        )

    new_fields = data.get("new_fields", [])
    dropped_fields = data.get("dropped_fields", [])
    cardinality = data.get("cardinality_changes", [])

    if not new_fields and not dropped_fields and not cardinality:
        msg = Text.from_markup(
            f"[bold green]✨ Perfect Alignment: No schema drift detected for note type '{escape(str(note_type))}'.[/bold green]\n\n"
            "[dim]All note instances adhere strictly to the schema specification.[/dim]"
        )
        return Panel(
            msg,
            title=f"📊 Schema Drift: {escape(str(note_type))}",
            title_align="left",
            border_style="green",
            padding=(1, 2),
        )

    elements = []
    if new_fields:
        table_new = Table(
            title="[bold green]New Fields (Observed in notes, missing from schema)[/bold green]",
            box=box.ROUNDED,
            expand=True,
        )
        table_new.add_column("Field Name", style="bold cyan")
        table_new.add_column("Source", style="magenta")
        table_new.add_column("Occurrence", justify="right")
        table_new.add_column("Percentage", justify="right")
        for f in new_fields:
            if isinstance(f, BaseModel):
                f = f.model_dump()
            elif not isinstance(f, dict):
                continue
            pct = f"{f.get('percentage', 0.0) * 100:.1f}%" if isinstance(f.get("percentage"), (int, float)) else str(f.get("percentage", ""))
            table_new.add_row(
                escape(str(f.get("name", ""))),
                escape(str(f.get("source", "observation"))),
                f"{f.get('count', 0)}/{f.get('total', 0)}",
                pct,
            )
        elements.append(table_new)

    if dropped_fields:
        table_drop = Table(
            title="[bold red]Dropped Fields (Defined in schema, absent from notes)[/bold red]",
            box=box.ROUNDED,
            expand=True,
        )
        table_drop.add_column("Field Name", style="bold cyan")
        table_drop.add_column("Source", style="magenta")
        table_drop.add_column("Occurrence", justify="right")
        table_drop.add_column("Missing %", justify="right")
        for f in dropped_fields:
            if isinstance(f, BaseModel):
                f = f.model_dump()
            elif not isinstance(f, dict):
                continue
            pct = f"{f.get('percentage', 0.0) * 100:.1f}%" if isinstance(f.get("percentage"), (int, float)) else str(f.get("percentage", ""))
            table_drop.add_row(
                escape(str(f.get("name", ""))),
                escape(str(f.get("source", "observation"))),
                f"{f.get('count', 0)}/{f.get('total', 0)}",
                pct,
            )
        elements.append(table_drop)

    return Panel(
        Group(*elements),
        title=f"📊 Schema Drift Analysis: {escape(str(note_type))}",
        title_align="left",
        border_style="yellow",
        padding=(1, 2),
    )


def _int(val: Any, default: int = 0) -> int:
    """Safely convert any value to int with fallback default."""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def render_lint_all_dashboard(results: Any) -> Panel:
    """Render unified 'Lint All' health dashboard."""
    if isinstance(results, BaseModel):
        results = results.model_dump()
    elif not isinstance(results, dict):
        results = {}

    raw_score = results.get("health_score")
    score: Optional[int] = _int(raw_score) if raw_score is not None else None
    doctor_passed = results.get("doctor_passed", True)
    if "doctor" in results and isinstance(results["doctor"], dict):
        doctor_passed = results["doctor"].get("passed", False) or results["doctor"].get("status") == "passed"

    schema_data = results.get("schema", {})
    if isinstance(schema_data, BaseModel):
        schema_data = schema_data.model_dump()
    elif not isinstance(schema_data, dict):
        schema_data = {}

    valid_count = _int(schema_data.get("valid_count", results.get("valid_schemas", 0)))
    total_notes = _int(schema_data.get("total_notes", results.get("total_notes", 0)))
    warnings = _int(schema_data.get("warning_count", results.get("schema_warnings", 0)))
    errors = _int(schema_data.get("error_count", results.get("schema_errors", 0)))

    orphans = results.get("orphans", [])
    orphan_count = len(orphans) if isinstance(orphans, list) else _int(results.get("orphan_count", 0))

    drift_data = results.get("drift", {})
    drift_count = _int(results.get("drift_count", 0))
    if isinstance(drift_data, dict):
        new_f = drift_data.get("new_fields", [])
        drop_f = drift_data.get("dropped_fields", [])
        drift_count += (len(new_f) if isinstance(new_f, list) else 0) + (len(drop_f) if isinstance(drop_f, list) else 0)

    if score is None:
        doc_pts = 30 if doctor_passed else 0
        schema_ratio = (valid_count / max(total_notes, 1)) if total_notes > 0 else 1.0
        schema_pts = max(0, int(40 * schema_ratio - (errors * 10) - (warnings * 2)))
        orphan_ratio = min(1.0, orphan_count / max(total_notes, 1)) if total_notes > 0 else (0.0 if orphan_count == 0 else 0.5)
        orphan_pts = max(0, int(20 * (1.0 - orphan_ratio)))
        drift_pts = max(0, 10 - min(10, drift_count * 2))
        score = max(0, min(100, doc_pts + schema_pts + orphan_pts + drift_pts))

    grade = results.get("grade")
    if not grade:
        if score >= 90:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 60:
            grade = "C"
        else:
            grade = "F"

    grade_colors = {"A": "bold green", "B": "bold cyan", "C": "bold yellow", "F": "bold red"}
    g_color = grade_colors.get(grade, "bold white")

    header = Text.from_markup(
        f"Overall Health Score: [bold]{score}/100[/bold]  |  Grade: [{g_color}]{grade}[/{g_color}]\n"
    )

    table = Table(box=box.ROUNDED, expand=True)
    table.add_column("Diagnostic Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    doc_status = "[bold green]PASS[/bold green]" if doctor_passed else "[bold red]FAIL[/bold red]"
    table.add_row(
        "1. Sync & Index Doctor",
        doc_status,
        "Database indexing & storage consistency verified" if doctor_passed else "Doctor checks failed",
    )

    schema_status = "[bold red]FAIL[/bold red]" if errors > 0 else ("[bold yellow]WARN[/bold yellow]" if warnings > 0 else "[bold green]PASS[/bold green]")
    table.add_row(
        "2. Schema Validation",
        schema_status,
        f"{valid_count}/{total_notes} valid, {warnings} warnings, {errors} errors",
    )

    orphan_status = "[bold green]CLEAN[/bold green]" if orphan_count == 0 else "[bold yellow]ORPHANS[/bold yellow]"
    table.add_row(
        "3. Graph Connectivity",
        orphan_status,
        f"{orphan_count} orphan entities without relations",
    )

    drift_status = "[bold green]ALIGNED[/bold green]" if drift_count == 0 else "[bold yellow]DRIFT[/bold yellow]"
    table.add_row(
        "4. Schema Drift",
        drift_status,
        f"{drift_count} drifting fields detected",
    )

    elements = [header, table]

    action_items = results.get("action_items", [])
    if action_items:
        action_text = Text("\nPrioritised Action Items:\n", style="bold")
        for item in action_items:
            action_text.append(f"  • {item}\n", style="yellow")
        elements.append(action_text)

    border_color = "green" if score >= 90 else ("yellow" if score >= 75 else "red")
    return Panel(
        Group(*elements),
        title="🏆 'Lint All' Diagnostic Health Dashboard",
        title_align="left",
        border_style=border_color,
        padding=(1, 2),
    )

