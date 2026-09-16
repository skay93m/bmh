from __future__ import annotations

import io
import pytest
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


def test_highlight_observations_public_and_status():
    from bmh.ui.cards import highlight_observations
    raw = "Status update: [status] in progress, completed: [X], todo: [todo]"
    highlighted = highlight_observations(raw)
    assert "[bold blue]\\[status][/bold blue]" in highlighted
    assert "[green]☑[/green]" in highlighted
    assert "[bold yellow]\\[todo][/bold yellow]" in highlighted


def test_render_note_card_with_observation_badges():
    note = NoteModel(
        title="Task Note",
        content="## Observations\n- [decision] Standardise on Rich\n- [risk] Complexity\n- [insight] Speed\n- [x] Step 1\n- [ ] Step 2",
    )
    panel = render_note_card(note)
    assert "Task Note" in panel.title

    # Verify rendering to console works cleanly and contains styled text
    buf = io.StringIO()
    test_console = Console(file=buf, force_terminal=True, width=100)
    test_console.print(panel)
    output = buf.getvalue()
    assert "[decision]" in output
    assert "[risk]" in output
    assert "[insight]" in output
    assert "☑" in output
    assert "☐" in output


def test_render_note_card_empty_content_and_no_metadata():
    note = NoteModel(title="Empty Note", content="")
    panel = render_note_card(note)
    assert panel.subtitle is None
    buf = io.StringIO()
    test_console = Console(file=buf, force_terminal=True, width=100)
    test_console.print(panel)
    assert "(No content)" in buf.getvalue()


def test_render_schema_validation_panel_clean():
    from bmh.ui.cards import render_schema_validation_panel
    data = {
        "total_notes": 10,
        "valid_count": 10,
        "warning_count": 0,
        "error_count": 0,
        "results": [],
    }
    panel = render_schema_validation_panel(data)
    assert "Schema Validation Report" in panel.title
    assert panel.border_style == "green"

    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    assert "All schemas valid with zero errors or warnings" in buf.getvalue()


def test_render_schema_validation_panel_with_issues():
    from bmh.ui.cards import render_schema_validation_panel
    data = {
        "total_notes": 2,
        "valid_count": 1,
        "warning_count": 1,
        "error_count": 1,
        "results": [
            {
                "note_identifier": "TASK-001",
                "schema_entity": "Task",
                "passed": False,
                "errors": ["Missing required field: description"],
                "warnings": [],
            },
            {
                "note_identifier": "TASK-002",
                "schema_entity": "Task",
                "passed": True,
                "errors": [],
                "warnings": ["Optional step missing"],
            },
        ],
    }
    panel = render_schema_validation_panel(data)
    assert panel.border_style == "red"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    out = buf.getvalue()
    assert "TASK-001" in out
    assert "TASK-002" in out
    assert "Missing required field: description" in out


def test_render_schema_validation_panel_error():
    from bmh.ui.cards import render_schema_validation_panel
    panel = render_schema_validation_panel({"error": "Unknown schema target 'foo'"})
    assert panel.border_style == "red"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    assert "Unknown schema target 'foo'" in buf.getvalue()


def test_render_orphan_list_panel_clean():
    from bmh.ui.cards import render_orphan_list_panel
    panel = render_orphan_list_panel([])
    assert panel.border_style == "green"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    assert "No orphan entities found" in buf.getvalue()


def test_render_orphan_list_panel_with_items():
    from bmh.ui.cards import render_orphan_list_panel
    orphans = [
        {
            "title": "Lonely Spec",
            "note_type": "spec",
            "file_path": "specs/lonely.md",
            "external_id": "ext-1",
        }
    ]
    panel = render_orphan_list_panel(orphans)
    assert panel.border_style == "yellow"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    out = buf.getvalue()
    assert "Lonely Spec" in out
    assert "specs/lonely.md" in out


def test_render_orphan_list_panel_error():
    from bmh.ui.cards import render_orphan_list_panel
    panel = render_orphan_list_panel([{"error": "Project not found"}])
    assert panel.border_style == "red"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    assert "Project not found" in buf.getvalue()


def test_render_doctor_panel_passed():
    from bmh.ui.cards import render_doctor_panel
    data = {
        "status": "passed",
        "passed": True,
        "steps": ["Created doctor project", "API write created file"],
        "output": "Doctor checks passed.",
    }
    panel = render_doctor_panel(data)
    assert panel.border_style == "green"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    out = buf.getvalue()
    assert "Healthy & Synced" in out
    assert "Created doctor project" in out


def test_render_doctor_panel_failed():
    from bmh.ui.cards import render_doctor_panel
    data = {
        "status": "failed",
        "passed": False,
        "steps": [],
        "output": "Doctor failed: index corrupted",
    }
    panel = render_doctor_panel(data)
    assert panel.border_style == "red"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    assert "Doctor failed: index corrupted" in buf.getvalue()


def test_render_schema_diff_panel_perfect_alignment():
    from bmh.ui.cards import render_schema_diff_panel
    data = {
        "note_type": "Task",
        "schema_found": True,
        "new_fields": [],
        "dropped_fields": [],
    }
    panel = render_schema_diff_panel(data)
    assert panel.border_style == "green"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    assert "Perfect Alignment" in buf.getvalue()


def test_render_schema_diff_panel_drift_detected():
    from bmh.ui.cards import render_schema_diff_panel
    data = {
        "note_type": "Task",
        "schema_found": True,
        "new_fields": [{"name": "cadence", "source": "observation", "count": 2, "total": 4, "percentage": 0.5}],
        "dropped_fields": [{"name": "steps", "source": "observation", "count": 0, "total": 4, "percentage": 0.0}],
    }
    panel = render_schema_diff_panel(data)
    assert panel.border_style == "yellow"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    out = buf.getvalue()
    assert "cadence" in out
    assert "steps" in out
    assert "50.0%" in out


def test_render_schema_diff_panel_schema_not_found():
    from bmh.ui.cards import render_schema_diff_panel
    panel = render_schema_diff_panel({"note_type": "Unknown", "schema_found": False})
    assert panel.border_style == "yellow"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    assert "No schema definition found" in buf.getvalue()


def test_render_schema_diff_panel_error():
    from bmh.ui.cards import render_schema_diff_panel
    panel = render_schema_diff_panel({"error": "Diff failed"})
    assert panel.border_style == "red"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    assert "Diff failed" in buf.getvalue()


def test_render_lint_all_dashboard_grade_a():
    from bmh.ui.cards import render_lint_all_dashboard
    results = {
        "health_score": 95,
        "grade": "A",
        "doctor_passed": True,
        "schema": {"valid_count": 10, "total_notes": 10, "warning_count": 0, "error_count": 0},
        "orphans": [],
        "drift_count": 0,
        "action_items": [],
    }
    panel = render_lint_all_dashboard(results)
    assert panel.border_style == "green"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    out = buf.getvalue()
    assert "95/100" in out
    assert "Grade: A" in out


def test_render_lint_all_dashboard_auto_score_and_action_items():
    from bmh.ui.cards import render_lint_all_dashboard
    results = {
        "doctor": {"status": "failed", "passed": False},
        "schema": {"valid_count": 1, "total_notes": 5, "warning_count": 2, "error_count": 2},
        "orphans": [{"title": "O1"}, {"title": "O2"}],
        "drift": {"new_fields": [{"name": "f1"}]},
        "action_items": ["Run doctor fix", "Add description to task"],
    }
    panel = render_lint_all_dashboard(results)
    assert panel.border_style == "red"
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=120).print(panel)
    out = buf.getvalue()
    assert "Grade: F" in out
    assert "Run doctor fix" in out
    assert "Add description to task" in out


def test_note_model_dict_access():
    note = NoteModel(title="Dict Note", content="Body", metadata={"custom_key": "custom_val"})
    assert note["title"] == "Dict Note"
    assert note["custom_key"] == "custom_val"
    assert note.get("title") == "Dict Note"
    assert note.get("custom_key") == "custom_val"
    assert note.get("missing", "default") == "default"
    assert "title" in note
    assert "custom_key" in note
    assert "missing" not in note
    keys = note.keys()
    assert "title" in keys
    assert "custom_key" in keys

    with pytest.raises(KeyError):
        _ = note["nonexistent_key"]


def test_extract_task_items():
    from bmh.core.models import extract_task_items
    content = """
# Task Heading
1. [ ] First step to do
2. [x] Second step completed
- [ ] Third bullet step
* [X] Fourth star completed
Normal text line
"""
    items = extract_task_items(content)
    assert len(items) == 4
    assert items[0].index == 1
    assert items[0].text == "First step to do"
    assert items[0].completed is False

    assert items[1].index == 2
    assert items[1].text == "Second step completed"
    assert items[1].completed is True

    assert items[2].index == 3
    assert items[2].text == "Third bullet step"
    assert items[2].completed is False

    assert items[3].index == 4
    assert items[3].text == "Fourth star completed"
    assert items[3].completed is True


def test_diagnostic_pydantic_models_with_card_renderers():
    from bmh.core.models import (
        DoctorReport,
        FieldValidationResult,
        LintAllSummary,
        NoteTemplate,
        NoteValidationResult,
        OrphanEntity,
        SchemaDiffReport,
        SchemaDriftField,
        SchemaValidationReport,
    )
    from bmh.ui.cards import (
        render_doctor_panel,
        render_lint_all_dashboard,
        render_orphan_list_panel,
        render_schema_diff_panel,
        render_schema_validation_panel,
    )

    # 1. SchemaValidationReport
    val_report = SchemaValidationReport(
        total_notes=1,
        total_entities=1,
        valid_count=1,
        results=[
            NoteValidationResult(
                note_identifier="TASK-01",
                schema_entity="Task",
                passed=True,
                field_results=[FieldValidationResult(field_name="desc", status="present")],
            )
        ],
    )
    p1 = render_schema_validation_panel(val_report)
    assert p1.border_style == "green"

    # 2. OrphanEntity
    orphans = [OrphanEntity(title="O1", note_type="task", file_path="t.md", external_id="e-1")]
    p2 = render_orphan_list_panel(orphans)
    assert p2.border_style == "yellow"

    # 3. DoctorReport
    doc_report = DoctorReport(status="passed", passed=True, output="ok", steps=["Step 1", "Step 2"])
    p3 = render_doctor_panel(doc_report)
    assert p3.border_style == "green"

    # 4. SchemaDiffReport
    diff_report = SchemaDiffReport(
        note_type="Task",
        schema_found=True,
        new_fields=[SchemaDriftField(name="custom_field", percentage=0.25)],
    )
    p4 = render_schema_diff_panel(diff_report)
    assert p4.border_style == "yellow"

    # 5. LintAllSummary
    lint_summary = LintAllSummary(
        health_score=92,
        grade="A",
        doctor_passed=True,
        valid_schemas=5,
        total_notes=5,
        action_items=["Clean up orphan"],
    )
    p5 = render_lint_all_dashboard(lint_summary)
    assert p5.border_style == "green"

    # 6. NoteTemplate
    tmpl = NoteTemplate(name="Task", folder="tasks", note_type="task", description="A task template", default_tags=["task"])
    assert tmpl.name == "Task"


def test_cards_renderers_non_dict_fallback():
    from bmh.ui.cards import (
        render_doctor_panel,
        render_lint_all_dashboard,
        render_schema_diff_panel,
        render_schema_validation_panel,
    )

    p1 = render_schema_validation_panel("invalid")
    assert "Schema Validation Report" in p1.title

    p2 = render_doctor_panel("invalid")
    assert "Basic Memory Doctor" in p2.title

    p3 = render_schema_diff_panel("invalid")
    assert "Schema Drift" in p3.title

    p4 = render_lint_all_dashboard("invalid")
    assert "'Lint All'" in p4.title


def test_lint_all_dashboard_grade_b_and_c():
    from bmh.ui.cards import render_lint_all_dashboard

    # Grade B (75-89)
    p_b = render_lint_all_dashboard({"health_score": 80})
    buf_b = io.StringIO()
    Console(file=buf_b, force_terminal=False, width=120).print(p_b)
    assert "Grade: B" in buf_b.getvalue()

    # Grade C (60-74)
    p_c = render_lint_all_dashboard({"health_score": 65})
    buf_c = io.StringIO()
    Console(file=buf_c, force_terminal=False, width=120).print(p_c)
    assert "Grade: C" in buf_c.getvalue()




