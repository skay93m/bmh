from __future__ import annotations

import io
from rich.console import Console
from bmh.core.models import NoteModel
from bmh.ui.cards import (
    _format_date,
    _highlight_observations,
    render_note_card,
    render_note_cards,
)


def test_highlight_observations():
    raw = "Here is a [decision] and an [insight] with a [risk] and [todo]."
    highlighted = _highlight_observations(raw)
    assert "[bold green]\\[decision][/bold green]" in highlighted
    assert "[bold magenta]\\[insight][/bold magenta]" in highlighted
    assert "[bold red]\\[risk][/bold red]" in highlighted
    assert "[bold yellow]\\[todo][/bold yellow]" in highlighted


def test_highlight_checkboxes():
    raw = "- [x] Done step\n- [ ] Pending step"
    highlighted = _highlight_observations(raw)
    assert "[green]☑[/green]" in highlighted
    assert "[dim]☐[/dim]" in highlighted


def test_format_date_variations():
    assert _format_date("2026-09-15T12:30:00Z") == "15/09/26 12:30"
    assert _format_date("2026-09-15") == "15/09/26"
    assert _format_date("invalid-date") == "invalid-date"
    assert _format_date(None) is None


def test_render_note_card_panel_properties():
    note = NoteModel(
        title="Sample Note",
        content="## Subheading\nSome body text.",
        entity="kancil:notes/sample.md",
        external_id="ext-1234",
        file_path="notes/sample.md",
        updated_at="2026-09-15T10:00:00Z",
    )
    panel = render_note_card(note, index=1, total=2)
    assert "Sample Note [1/2]" in panel.title
    assert "entity:" in panel.subtitle
    assert "kancil:notes/sample.md" in panel.subtitle
    assert "external_id:" in panel.subtitle
    assert "ext-1234" in panel.subtitle
    assert "updated:" in panel.subtitle


def test_render_note_cards_output():
    buf = io.StringIO()
    test_console = Console(file=buf, force_terminal=True, width=100)

    notes = [
        NoteModel(title="First Note", content="First content"),
        NoteModel(title="Second Note", content="Second content"),
    ]

    render_note_cards(notes, custom_console=test_console)
    output = buf.getvalue()

    assert "First Note" in output
    assert "Second Note" in output
    assert "[1/2]" in output
    assert "[2/2]" in output


def test_render_empty_note_cards():
    buf = io.StringIO()
    test_console = Console(file=buf, force_terminal=True, width=100)

    render_note_cards([], custom_console=test_console)
    output = buf.getvalue()
    assert "No notes found matching criteria." in output
