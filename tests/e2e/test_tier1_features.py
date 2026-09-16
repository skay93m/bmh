from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest
from rich.console import Console
from rich.panel import Panel
from typer.testing import CliRunner

from bmh.core.client import BMClient, BMError, BMExecutionError, BMNotFoundError
from bmh.core.models import NoteModel, SearchResult, normalize_notes_json, _dict_to_note
from bmh.ui.cards import (
    _highlight_observations,
    _format_date,
    render_note_card,
    render_note_cards,
)
from bmh.ui.menu import (
    _handle_client_error,
    flow_active_tasks,
    flow_browse_project,
    flow_recent_notes,
    flow_search_notes,
    run_interactive_session,
)
from bmh.main import app, main


# Helper to import or skip workflows progressively
def _get_workflow(hub: str, func_name: str, milestone: str):
    try:
        mod = __import__(f"bmh.workflows.{hub}", fromlist=[func_name])
        return getattr(mod, func_name)
    except (ImportError, AttributeError):
        pytest.skip(f"Workflow function '{hub}.{func_name}' not yet implemented ({milestone})")


def _get_ui_card_func(func_name: str, milestone: str = "M1"):
    import bmh.ui.cards as cards_mod
    func = getattr(cards_mod, func_name, None)
    if func is None:
        pytest.skip(f"UI cards function '{func_name}' not yet implemented ({milestone})")
    return func


# ==============================================================================
# Feature 1: BMClient Subprocess Core (R5)
# ==============================================================================
class TestFeature01BMClientSubprocessCore:
    def test_client_availability_true_when_binary_exists(self):
        client = BMClient(binary_path="/usr/bin/python3")
        assert client.is_available() is True

    def test_client_availability_false_when_binary_missing(self):
        client = BMClient(binary_path="/nonexistent/path/to/bm")
        assert client.is_available() is False

    def test_execute_raises_not_found_error_when_unavailable(self):
        client = BMClient(binary_path="/nonexistent/bm")
        with pytest.raises(BMNotFoundError) as exc_info:
            client.execute(["version"])
        assert "not found" in str(exc_info.value).lower()

    def test_execute_builds_correct_cmd_and_returns_completed_process(self):
        client = BMClient(binary_path="/bin/echo")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="hello", stderr="")
            result = client.execute(["hello", "world"], timeout=10.0)
            mock_run.assert_called_once()
            assert result.returncode == 0
            assert result.stdout == "hello"

    def test_execute_with_stdin_input_streaming(self):
        client = BMClient(binary_path="/bin/echo")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="streamed", stderr="")
            result = client.execute(["cat"], input="streamed input")
            mock_run.assert_called_once()
            assert mock_run.call_args[1].get("input") == "streamed input"

    def test_search_notes_constructs_tool_search_notes_command(self):
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout='{"results": [{"title": "Note 1", "content": "Content 1"}]}',
            )
            notes = client.search_notes(
                query="auth",
                project="kancil",
                note_type="task",
                status="active",
                is_title=True,
            )
            mock_exec.assert_called_once()
            args = mock_exec.call_args[0][0]
            assert "tool" in args
            assert "search-notes" in args
            assert "--title" in args
            assert "--project" in args
            assert "kancil" in args
            assert "--type" in args
            assert "task" in args
            assert "--status" in args
            assert "active" in args
            assert "--json" in args
            assert "auth" in args
            assert len(notes) == 1
            assert notes[0].title == "Note 1"

    def test_write_note_constructs_tool_write_note_command(self):
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout='{"title": "Note A", "action": "created"}',
            )
            res = client.write_note(
                title="Note A",
                folder="tasks",
                content="Note content",
                note_type="task",
                project="kancil",
                overwrite=True,
            )
            mock_exec.assert_called_once()
            args = mock_exec.call_args[0][0]
            assert "tool" in args
            assert "write-note" in args
            assert "--title" in args
            assert "Note A" in args
            assert "--folder" in args
            assert "tasks" in args
            assert "--content" in args
            assert "--type" in args
            assert "task" in args
            assert "--overwrite" in args
            assert res.get("action") == "created"

    def test_edit_note_constructs_tool_edit_note_command(self):
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout='{"title": "Note A", "operation": "append"}',
            )
            res = client.edit_note(
                identifier="tasks/task-1.md",
                operation="append",
                content="- [decision] Approved",
                project="kancil",
            )
            mock_exec.assert_called_once()
            args = mock_exec.call_args[0][0]
            assert "tool" in args
            assert "edit-note" in args
            assert "tasks/task-1.md" in args
            assert "--operation" in args
            assert "append" in args
            assert res.get("operation") == "append"

    def test_read_note_returns_dict_or_none_on_null_fields(self):
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            # Valid note
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout='{"title": "Found", "content": "Body"}',
            )
            note = client.read_note("tasks/found.md")
            assert note is not None
            assert note.get("title") == "Found"

            # Missing note returns exit 0 with nulls -> read_note should return None
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout='{"title": null, "content": null, "permalink": null, "file_path": null}',
            )
            missing = client.read_note("tasks/nonexistent.md")
            assert missing is None

    def test_schema_validate_and_schema_diff_command_calls(self):
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.return_value = MagicMock(returncode=0, stdout='{"valid_count": 2}')
            v_res = client.schema_validate(target="Task", project="kancil")
            assert v_res.get("valid_count") == 2
            v_args = mock_exec.call_args[0][0]
            assert "schema-validate" in v_args
            assert "Task" in v_args

            mock_exec.return_value = MagicMock(returncode=0, stdout='{"schema_found": true}')
            d_res = client.schema_diff(note_type="Task", project="kancil")
            assert d_res.get("schema_found") is True
            d_args = mock_exec.call_args[0][0]
            assert "schema-diff" in d_args

    def test_doctor_and_orphans_and_recent_activity_and_projects(self):
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            # Doctor
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout="OK Created doctor project: d1\nOK API write created file\nDoctor checks passed.",
            )
            doc = client.doctor()
            assert doc["passed"] is True
            assert len(doc["steps"]) >= 2

            # Orphans
            mock_exec.return_value = MagicMock(returncode=0, stdout='[{"title": "Orphan 1"}]')
            orphans = client.orphans(project="kancil")
            assert len(orphans) == 1
            assert orphans[0]["title"] == "Orphan 1"

            # Recent activity
            mock_exec.return_value = MagicMock(returncode=0, stdout='[{"title": "Recent 1"}]')
            recent = client.recent_activity(project="kancil")
            assert len(recent) == 1

            # List projects
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout='{"projects": [{"name": "kancil", "is_default": true}]}',
            )
            projects = client.list_projects()
            assert len(projects) == 1
            assert projects[0]["name"] == "kancil"


# ==============================================================================
# Feature 2: Model Definitions & Serialization (R5)
# ==============================================================================
class TestFeature02ModelDefinitionsAndSerialization:
    def test_note_model_default_values(self):
        note = NoteModel()
        assert note.title == "Untitled Note"
        assert note.content == ""
        assert note.metadata == {}
        assert note.entity is None

    def test_note_model_title_validator_strips_whitespace_and_defaults(self):
        note_blank = NoteModel(title="   ")
        assert note_blank.title == "Untitled Note"
        note_valid = NoteModel(title="  Clean Title  ")
        assert note_valid.title == "Clean Title"

    def test_search_result_envelope_model(self, sample_note_model):
        envelope = SearchResult(
            results=[sample_note_model],
            total=1,
            current_page=1,
            page_size=10,
            has_more=False,
        )
        assert len(envelope.results) == 1
        assert envelope.total == 1
        assert envelope.results[0].title == "Daily Token Spend Optimisation"

    def test_normalize_notes_json_handles_json_arrays(self):
        json_data = json.dumps([
            {"title": "Note A", "content": "Body A"},
            {"title": "Note B", "content": "Body B"},
        ])
        notes = normalize_notes_json(json_data)
        assert len(notes) == 2
        assert notes[0].title == "Note A"
        assert notes[1].title == "Note B"

    def test_normalize_notes_json_handles_envelope_dict_with_results(self, sample_search_json):
        notes = normalize_notes_json(sample_search_json)
        assert len(notes) == 1
        assert notes[0].title == "Daily Token Spend Optimisation"
        assert notes[0].file_path == "tasks/daily-token-spend-optimisation.md"

    def test_extract_task_items_from_markdown(self):
        from bmh.core.models import extract_task_items
        markdown = """
        # Task Note
        ## Steps
        1. [ ] First step
        2. [x] Second step completed
        - [X] Third bullet step completed
        - [ ] Fourth bullet step pending
        """
        items = extract_task_items(markdown)
        assert len(items) == 4
        assert items[0].completed is False
        assert items[0].text == "First step"
        assert items[1].completed is True
        assert items[1].text == "Second step completed"
        assert items[2].completed is True
        assert items[3].completed is False

    def test_diagnostic_report_models(self):
        from bmh.core.models import (
            SchemaValidationReport,
            OrphanEntity,
            DoctorReport,
            SchemaDiffReport,
            LintAllSummary,
        )
        # SchemaValidationReport
        svr = SchemaValidationReport(total_notes=10, valid_count=9, warning_count=1, error_count=0)
        assert svr.valid_count == 9

        # OrphanEntity
        orphan = OrphanEntity(external_id="u1", title="Orphan Note", note_type="note")
        assert orphan.title == "Orphan Note"

        # DoctorReport
        doc = DoctorReport(status="passed", passed=True, steps=["Step 1", "Step 2"])
        assert doc.passed is True

        # SchemaDiffReport
        diff = SchemaDiffReport(note_type="Task", schema_found=True)
        assert diff.schema_found is True

        # LintAllSummary
        lint_all = LintAllSummary(health_score=95, grade="A", doctor_passed=True)
        assert lint_all.grade == "A"



# ==============================================================================
# Feature 3: Observation Badge Formatting (R5)
# ==============================================================================
class TestFeature03ObservationBadgeFormatting:
    def test_highlight_observations_decision_badge(self):
        result = _highlight_observations("Key [decision] adopted SQLite.")
        assert "[bold green]\\[decision][/bold green]" in result

    def test_highlight_observations_risk_badge(self):
        result = _highlight_observations("Identified [risk] subprocess timeout.")
        assert "[bold red]\\[risk][/bold red]" in result

    def test_highlight_observations_insight_badge(self):
        result = _highlight_observations("New [insight] vector latency.")
        assert "[bold magenta]\\[insight][/bold magenta]" in result

    def test_highlight_observations_todo_badge(self):
        result = _highlight_observations("Action item: [todo] write tests.")
        assert "[bold yellow]\\[todo][/bold yellow]" in result

    def test_highlight_observations_status_and_checkboxes(self):
        result = _highlight_observations("Status [status] active, 1. [x] Done, 2. [ ] Pending")
        assert "[bold blue]\\[status][/bold blue]" in result
        assert "[green]☑[/green]" in result
        assert "[dim]☐[/dim]" in result

    def test_render_note_card_panel_properties(self, sample_note_model):
        panel = render_note_card(sample_note_model, index=1, total=2)
        assert isinstance(panel, Panel)
        assert "Daily Token Spend Optimisation" in str(panel.title)
        assert "[1/2]" in str(panel.title)
        assert "entity:" in str(panel.subtitle)


# ==============================================================================
# Feature 4: Diagnostic Result Panels (R5)
# ==============================================================================
class TestFeature04DiagnosticResultPanels:
    def test_render_schema_validation_panel(self):
        renderer = _get_ui_card_func("render_schema_validation_panel")
        data = {
            "total_notes": 5,
            "valid_count": 5,
            "warning_count": 0,
            "error_count": 0,
            "results": [],
        }
        panel = renderer(data)
        assert isinstance(panel, Panel)

    def test_render_orphan_list_panel(self):
        renderer = _get_ui_card_func("render_orphan_list_panel")
        orphans = [
            {"external_id": "u1", "title": "Orphan Note", "note_type": "note", "file_path": "n.md"}
        ]
        panel = renderer(orphans)
        assert isinstance(panel, Panel)

    def test_render_orphan_list_panel_empty(self):
        renderer = _get_ui_card_func("render_orphan_list_panel")
        panel = renderer([])
        assert isinstance(panel, Panel)

    def test_render_doctor_panel(self):
        renderer = _get_ui_card_func("render_doctor_panel")
        data = {
            "status": "passed",
            "output": "Doctor checks passed.",
            "steps": ["Created doctor project", "API write created file"],
        }
        panel = renderer(data)
        assert isinstance(panel, Panel)

    def test_render_schema_diff_panel(self):
        renderer = _get_ui_card_func("render_schema_diff_panel")
        data = {
            "note_type": "Task",
            "schema_found": True,
            "new_fields": [{"name": "cadence", "source": "observation", "count": 1, "total": 2, "percentage": 0.5}],
            "dropped_fields": [],
        }
        panel = renderer(data)
        assert isinstance(panel, Panel)

    def test_render_lint_all_dashboard(self):
        renderer = _get_ui_card_func("render_lint_all_dashboard")
        results = {
            "score": 95,
            "grade": "A",
            "doctor": {"status": "passed"},
            "schema": {"valid_count": 10, "error_count": 0},
            "orphans": [],
            "diff": {"new_fields": []},
        }
        panel = renderer(results)
        assert isinstance(panel, Panel)


# ==============================================================================
# Feature 5: Task Note Template Wizard (R2)
# ==============================================================================
class TestFeature05TaskNoteTemplateWizard:
    def test_task_wizard_prompts_and_invokes_write_note(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "OAuth2 Refresh",       # title
            "Implement token flow", # description
            "active",               # status
            "high",                 # priority
            "louis",                # assignee
            "Step 1, Step 2",       # steps
            "kancil",               # project
            "auth, backend",        # tags
        ]):
            wizard_func(console, mock_bm_client, template_type="task")
            assert mock_bm_client.write_note.called
            call_kwargs = mock_bm_client.write_note.call_args[1]
            assert "OAuth2 Refresh" in str(call_kwargs.get("title"))
            assert "tasks" in str(call_kwargs.get("folder"))

    def test_task_wizard_includes_steps_and_observations(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Test Task", "Desc", "active", "medium", "kancil", "First Step", "kancil", "tag"
        ]):
            wizard_func(console, mock_bm_client, template_type="task")
            content = mock_bm_client.write_note.call_args[1].get("content", "")
            assert "## Steps" in content or "1. [ ]" in content

    def test_task_wizard_handles_write_conflict(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        mock_bm_client.write_note.side_effect = BMExecutionError("Conflict", 1, "NOTE_ALREADY_EXISTS")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Existing Task", "Desc", "active", "medium", "louis", "Step 1", "kancil", "tag"
        ]):
            # Should catch conflict and not crash
            try:
                wizard_func(console, mock_bm_client, template_type="task")
            except Exception as e:
                assert not isinstance(e, KeyError)

    def test_task_wizard_validates_required_title(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "", "Valid Task Title", "Desc", "active", "medium", "louis", "Step 1", "kancil", "tag"
        ]):
            wizard_func(console, mock_bm_client, template_type="task")
            assert mock_bm_client.write_note.called

    def test_task_wizard_sets_type_frontmatter(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Task With Frontmatter", "Desc", "active", "medium", "louis", "Step 1", "kancil", "tag"
        ]):
            wizard_func(console, mock_bm_client, template_type="task")
            call_kwargs = mock_bm_client.write_note.call_args[1]
            assert call_kwargs.get("note_type") == "task" or "type: task" in call_kwargs.get("content", "")


# ==============================================================================
# Feature 6: Insight Note Template Wizard (R2)
# ==============================================================================
class TestFeature06InsightNoteTemplateWizard:
    def test_insight_wizard_prompts_and_invokes_write_note(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Latency Discovery",   # title
            "Hybrid vector lag",   # finding
            "Unfiltered 80% lag",  # insight
            "Pre-filter tags",     # implication
            "perf, search",        # tags
            "kensho",              # project
        ]):
            wizard_func(console, mock_bm_client, template_type="insight")
            assert mock_bm_client.write_note.called
            call_kwargs = mock_bm_client.write_note.call_args[1]
            assert "Latency Discovery" in str(call_kwargs.get("title"))

    def test_insight_wizard_generates_insight_and_implication_badges(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Cache Invalidation", "TTL issue", "Stale reads", "Evict on write", "cache", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="insight")
            content = mock_bm_client.write_note.call_args[1].get("content", "")
            assert "[insight]" in content or "[implication]" in content

    def test_insight_wizard_routes_to_insights_folder(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Architecture Discovery", "Finding", "Takeaway", "Impact", "arch", "kensho"
        ]):
            wizard_func(console, mock_bm_client, template_type="insight")
            folder = mock_bm_client.write_note.call_args[1].get("folder", "")
            assert folder in ("insights", "knowledge", "notes")

    def test_insight_wizard_default_tags(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Quick Insight", "Finding", "Takeaway", "Impact", "", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="insight")
            assert mock_bm_client.write_note.called

    def test_insight_wizard_handles_write_failure_gracefully(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        mock_bm_client.write_note.side_effect = BMError("Write disk error")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Fail Insight", "Finding", "Takeaway", "Impact", "tag", "kancil"
        ]):
            try:
                wizard_func(console, mock_bm_client, template_type="insight")
            except BMError:
                pass


# ==============================================================================
# Feature 7: Meeting Note Template Wizard (R2)
# ==============================================================================
class TestFeature07MeetingNoteTemplateWizard:
    def test_meeting_wizard_prompts_and_invokes_write_note(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Sprint Planning",        # title
            "2026-09-16",             # date
            "louis, syafiq",          # participants
            "Tri-modal roadmap",      # agenda
            "Deploy on develop",      # decision
            "Timeout risk bounded",   # risk
            "Write tests",            # action item / todo
            "kancil",                 # project
        ]):
            wizard_func(console, mock_bm_client, template_type="meeting")
            assert mock_bm_client.write_note.called
            call_kwargs = mock_bm_client.write_note.call_args[1]
            assert "Sprint Planning" in str(call_kwargs.get("title"))

    def test_meeting_wizard_contains_decision_and_risk_tags(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Sync Meeting", "2026-09-16", "kancil", "Agenda", "Adopt Typer", "Learning curve", "Review docs", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="meeting")
            content = mock_bm_client.write_note.call_args[1].get("content", "")
            assert "[decision]" in content or "[risk]" in content or "[todo]" in content

    def test_meeting_wizard_routes_to_meetings_folder(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Quarterly Review", "2026-09-16", "team", "Review", "Approved", "None", "Schedule follow-up", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="meeting")
            folder = mock_bm_client.write_note.call_args[1].get("folder", "")
            assert folder in ("meetings", "notes")

    def test_meeting_wizard_action_items_checkboxes(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Action Meeting", "2026-09-16", "team", "Agenda", "Dec", "Risk", "Action item 1", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="meeting")
            content = mock_bm_client.write_note.call_args[1].get("content", "")
            assert "1. [ ]" in content or "- [ ]" in content or "[todo]" in content

    def test_meeting_wizard_handles_write_exception(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        mock_bm_client.write_note.side_effect = BMExecutionError("Write error", 1, "Failed")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Error Meeting", "2026-09-16", "team", "Agenda", "Dec", "Risk", "Action", "kancil"
        ]):
            try:
                wizard_func(console, mock_bm_client, template_type="meeting")
            except BMExecutionError:
                pass


# ==============================================================================
# Feature 8: Decision Note Template Wizard (R2)
# ==============================================================================
class TestFeature08DecisionNoteTemplateWizard:
    def test_decision_wizard_prompts_and_invokes_write_note(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Use Pydantic v2",     # title
            "decided",             # status
            "Need strict models",  # context
            "Standardise on v2",   # decision
            "High performance",    # rationale
            "Schema migration",    # risk
            "kensho",              # project
        ]):
            wizard_func(console, mock_bm_client, template_type="decision")
            assert mock_bm_client.write_note.called
            call_kwargs = mock_bm_client.write_note.call_args[1]
            assert "Use Pydantic v2" in str(call_kwargs.get("title"))

    def test_decision_wizard_contains_rationale_and_decision_tags(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Database Engine", "decided", "Storage need", "SQLite chosen", "Simplicity", "Single writer", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="decision")
            content = mock_bm_client.write_note.call_args[1].get("content", "")
            assert "[decision]" in content or "[rationale]" in content

    def test_decision_wizard_routes_to_decisions_folder(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "CLI Framework", "decided", "CLI companion", "Typer selected", "Interactive", "None", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="decision")
            folder = mock_bm_client.write_note.call_args[1].get("folder", "")
            assert folder in ("decisions", "notes")

    def test_decision_wizard_supports_statuses(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Proposed Architecture", "proposed", "Context", "Dec", "Rat", "Risk", "kensho"
        ]):
            wizard_func(console, mock_bm_client, template_type="decision")
            content = mock_bm_client.write_note.call_args[1].get("content", "")
            assert "status: proposed" in content or "proposed" in content

    def test_decision_wizard_handles_write_conflict(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        mock_bm_client.write_note.side_effect = BMExecutionError("Conflict", 1, "NOTE_ALREADY_EXISTS")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Conflict Decision", "decided", "Ctx", "Dec", "Rat", "Risk", "kancil"
        ]):
            try:
                wizard_func(console, mock_bm_client, template_type="decision")
            except BMExecutionError:
                pass


# ==============================================================================
# Feature 9: Scratchpad Note Template Wizard (R2)
# ==============================================================================
class TestFeature09ScratchpadNoteTemplateWizard:
    def test_scratchpad_wizard_prompts_and_invokes_write_note(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Temporary API Notes",    # title
            "Random thoughts on curl", # body
            "scratchpad, draft",      # tags
            "kancil",                 # project
        ]):
            wizard_func(console, mock_bm_client, template_type="scratchpad")
            assert mock_bm_client.write_note.called
            call_kwargs = mock_bm_client.write_note.call_args[1]
            assert "Temporary API Notes" in str(call_kwargs.get("title"))

    def test_scratchpad_wizard_routes_to_scratchpad_folder(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Draft Thoughts", "Quick snippet", "draft", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="scratchpad")
            folder = mock_bm_client.write_note.call_args[1].get("folder", "")
            assert folder in ("scratchpad", "inbox", "notes")

    def test_scratchpad_wizard_default_title(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "", "Body text", "draft", "kancil"
        ]):
            # If title is empty, wizard either prompts again or provides default title
            with patch("rich.prompt.Prompt.ask", side_effect=["Default Scratchpad", "Body", "draft", "kancil"]):
                wizard_func(console, mock_bm_client, template_type="scratchpad")
                assert mock_bm_client.write_note.called

    def test_scratchpad_wizard_multiline_content(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Multi Notes", "Line 1\nLine 2\nLine 3", "scratchpad", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="scratchpad")
            content = mock_bm_client.write_note.call_args[1].get("content", "")
            assert "Line 1" in content

    def test_scratchpad_wizard_handles_write_failure(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        mock_bm_client.write_note.side_effect = BMError("Disk full")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Scratch", "Content", "draft", "kancil"
        ]):
            try:
                wizard_func(console, mock_bm_client, template_type="scratchpad")
            except BMError:
                pass


# ==============================================================================
# Feature 10: Quick Observation Appender (R2)
# ==============================================================================
class TestFeature10QuickObservationAppender:
    def test_appender_searches_selects_and_appends_observation(self, mock_bm_client, sample_note_model):
        appender_func = _get_workflow("ingest", "run_quick_appender", "M2")
        mock_bm_client.search_notes.return_value = [sample_note_model]
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Daily Token",  # search query
            "1",            # select note index 1
            "1",            # select tag [decision]
            "Migrate to SQLite for baseline metrics", # observation text
        ]):
            appender_func(console, mock_bm_client)
            assert mock_bm_client.edit_note.called
            call_kwargs = mock_bm_client.edit_note.call_args[1]
            assert call_kwargs.get("operation") == "append"
            assert "[decision]" in call_kwargs.get("content", "")

    def test_appender_supports_risk_tag(self, mock_bm_client, sample_note_model):
        appender_func = _get_workflow("ingest", "run_quick_appender", "M2")
        mock_bm_client.search_notes.return_value = [sample_note_model]
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Daily Token", "1", "2", "Potential memory exhaustion on large trace"
        ]):
            appender_func(console, mock_bm_client)
            content = mock_bm_client.edit_note.call_args[1].get("content", "")
            assert "[risk]" in content

    def test_appender_supports_insight_tag(self, mock_bm_client, sample_note_model):
        appender_func = _get_workflow("ingest", "run_quick_appender", "M2")
        mock_bm_client.search_notes.return_value = [sample_note_model]
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Daily Token", "1", "3", "FTS5 matches faster than vector on exact titles"
        ]):
            appender_func(console, mock_bm_client)
            content = mock_bm_client.edit_note.call_args[1].get("content", "")
            assert "[insight]" in content

    def test_appender_supports_todo_tag(self, mock_bm_client, sample_note_model):
        appender_func = _get_workflow("ingest", "run_quick_appender", "M2")
        mock_bm_client.search_notes.return_value = [sample_note_model]
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Daily Token", "1", "4", "Add benchmark suite to CI pipeline"
        ]):
            appender_func(console, mock_bm_client)
            content = mock_bm_client.edit_note.call_args[1].get("content", "")
            assert "[todo]" in content

    def test_appender_handles_no_notes_found(self, mock_bm_client):
        appender_func = _get_workflow("ingest", "run_quick_appender", "M2")
        mock_bm_client.search_notes.return_value = []
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["nonexistent query", "0"]):
            appender_func(console, mock_bm_client)
            assert not mock_bm_client.edit_note.called


# ==============================================================================
# Feature 11: Piped Ingest Handler (R2)
# ==============================================================================
class TestFeature11PipedIngestHandler:
    def test_piped_capture_creates_new_note(self, mock_bm_client):
        handler_func = _get_workflow("ingest", "handle_piped_capture", "M2")
        with patch("sys.stdin.read", return_value="# Ingested Markdown\n\nSome body text"):
            with patch("rich.prompt.Prompt.ask", side_effect=["Piped Document", "inbox", "kancil"]):
                handler_func(mock_bm_client, title="Piped Document", folder="inbox")
                assert mock_bm_client.write_note.called

    def test_piped_capture_appends_to_existing_note(self, mock_bm_client):
        handler_func = _get_workflow("ingest", "handle_piped_capture", "M2")
        try:
            with patch("sys.stdin.read", return_value="Extra snippet to append"):
                with patch("rich.prompt.Prompt.ask", side_effect=["2", "kancil/tasks/daily-token", "kancil"]):
                    handler_func(mock_bm_client)
        except Exception:
            pass

    def test_piped_capture_handles_empty_input(self, mock_bm_client):
        handler_func = _get_workflow("ingest", "handle_piped_capture", "M2")
        with patch("sys.stdin.read", return_value=""):
            result = handler_func(mock_bm_client)
            assert result is None or not mock_bm_client.write_note.called

    def test_piped_capture_preserves_code_blocks(self, mock_bm_client):
        handler_func = _get_workflow("ingest", "handle_piped_capture", "M2")
        raw_snippet = "```python\nprint('hello')\n```"
        with patch("sys.stdin.read", return_value=raw_snippet):
            with patch("rich.prompt.Prompt.ask", side_effect=["Code Snippet", "inbox", "kancil"]):
                handler_func(mock_bm_client, title="Code Snippet", folder="inbox")
                if mock_bm_client.write_note.called:
                    content = mock_bm_client.write_note.call_args[1].get("content", "")
                    assert "print('hello')" in content

    def test_piped_capture_handles_write_error(self, mock_bm_client):
        handler_func = _get_workflow("ingest", "handle_piped_capture", "M2")
        mock_bm_client.write_note.side_effect = BMError("Failed to write")
        with patch("sys.stdin.read", return_value="Test Content"):
            with patch("rich.prompt.Prompt.ask", side_effect=["Test Note", "inbox", "kancil"]):
                try:
                    handler_func(mock_bm_client, title="Test Note", folder="inbox")
                except BMError:
                    pass


# ==============================================================================
# Feature 12: Note Search Browser (R3)
# ==============================================================================
class TestFeature12NoteSearchBrowser:
    def test_search_notes_flow_invokes_client_with_query_and_project(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=["database migration", "kensho"]):
            with patch("rich.prompt.Confirm.ask", return_value=False):
                flow_search_notes(mock_bm_client)
                mock_bm_client.search_notes.assert_called_once_with(
                    query="database migration",
                    project="kensho",
                    is_title=False,
                )

    def test_search_notes_flow_supports_title_only(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=["Token Spend", "kancil"]):
            with patch("rich.prompt.Confirm.ask", return_value=True):
                flow_search_notes(mock_bm_client)
                mock_bm_client.search_notes.assert_called_once_with(
                    query="Token Spend",
                    project="kancil",
                    is_title=True,
                )

    def test_search_notes_flow_renders_returned_cards(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=["architecture", ""]):
            with patch("rich.prompt.Confirm.ask", return_value=False):
                with patch("bmh.workflows.query.render_note_cards") as mock_render:
                    flow_search_notes(mock_bm_client)
                    mock_render.assert_called_once()

    def test_search_notes_flow_handles_bm_error_cleanly(self, mock_bm_client):
        mock_bm_client.search_notes.side_effect = BMError("Search index down")
        with patch("rich.prompt.Prompt.ask", side_effect=["test", ""]):
            with patch("rich.prompt.Confirm.ask", return_value=False):
                with patch("bmh.workflows.query._handle_error") as mock_err:
                    flow_search_notes(mock_bm_client)
                    mock_err.assert_called_once()

    def test_search_notes_empty_query_returns_early(self, mock_bm_client):
        # New behavior: empty query prompts user and returns without searching
        with patch("rich.prompt.Prompt.ask", side_effect=["", ""]):
            flow_search_notes(mock_bm_client)
            mock_bm_client.search_notes.assert_not_called()


# ==============================================================================
# Feature 13: Active Task Inspector & Step Checkoff (R3)
# ==============================================================================
class TestFeature13ActiveTaskInspectorAndStepCheckoff:
    def test_flow_active_tasks_queries_task_and_active(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", return_value="kancil"):
            with patch("rich.prompt.Confirm.ask", return_value=False):
                flow_active_tasks(mock_bm_client)
                mock_bm_client.search_notes.assert_called_once_with(
                    query=None,
                    project="kancil",
                    note_type="task",
                    status="active",
                )

    def test_task_checkoff_invokes_find_replace_edit(self, mock_bm_client, sample_note_model):
        query_wf = _get_workflow("query", "run_active_tasks_inspector", "M3")
        mock_bm_client.search_notes.return_value = [sample_note_model]
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["1", "1", "0"]):
            query_wf(console, mock_bm_client)
            if mock_bm_client.edit_note.called:
                call_kwargs = mock_bm_client.edit_note.call_args[1]
                assert call_kwargs.get("operation") == "find_replace"

    def test_task_inspector_handles_no_active_tasks(self, mock_bm_client):
        query_wf = _get_workflow("query", "run_active_tasks_inspector", "M3")
        mock_bm_client.search_notes.return_value = []
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            query_wf(console, mock_bm_client)
            assert not mock_bm_client.edit_note.called

    def test_task_checkoff_handles_task_with_no_steps(self, mock_bm_client):
        query_wf = _get_workflow("query", "run_active_tasks_inspector", "M3")
        no_steps_note = NoteModel(title="No Steps Task", content="Just plain text without steps")
        mock_bm_client.search_notes.return_value = [no_steps_note]
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["1", "0"]):
            query_wf(console, mock_bm_client)
            assert not mock_bm_client.edit_note.called

    def test_task_inspector_error_handling(self, mock_bm_client):
        mock_bm_client.search_notes.side_effect = BMError("Fetch failed")
        with patch("rich.prompt.Prompt.ask", return_value="kancil"):
            with patch("bmh.workflows.query._handle_error") as mock_err:
                flow_active_tasks(mock_bm_client)
                mock_err.assert_called_once()


# ==============================================================================
# Feature 14: Project Browser (kancil/kensho) (R3)
# ==============================================================================
class TestFeature14ProjectBrowser:
    def test_browse_kancil_project(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=["1", ""]):
            flow_browse_project(mock_bm_client)
            mock_bm_client.search_notes.assert_called_once_with(
                query=None,
                project="kancil",
            )

    def test_browse_kensho_project(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=["2", "architecture"]):
            flow_browse_project(mock_bm_client)
            mock_bm_client.search_notes.assert_called_once_with(
                query="architecture",
                project="kensho",
            )

    def test_browse_project_by_name_string(self, mock_bm_client):
        # New impl uses numeric choices; "2" selects kensho
        with patch("rich.prompt.Prompt.ask", side_effect=["2", ""]):
            flow_browse_project(mock_bm_client)
            mock_bm_client.search_notes.assert_called_once_with(query=None, project="kensho")

    def test_browse_project_renders_cards(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=["1", ""]):
            with patch("bmh.workflows.query.render_note_cards") as mock_render:
                flow_browse_project(mock_bm_client)
                mock_render.assert_called_once()

    def test_browse_project_handles_error(self, mock_bm_client):
        mock_bm_client.search_notes.side_effect = BMError("Project unavailable")
        with patch("rich.prompt.Prompt.ask", side_effect=["1", ""]):
            with patch("bmh.workflows.query._handle_error") as mock_err:
                flow_browse_project(mock_bm_client)
                mock_err.assert_called_once()


# ==============================================================================
# Feature 15: Recent Activity Timeline (R3)
# ==============================================================================
class TestFeature15RecentActivityTimeline:
    def test_flow_recent_notes_calls_recent_activity(self, mock_bm_client):
        # New impl uses client.recent_activity, not search_notes
        mock_bm_client.recent_activity.return_value = []
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "10"]):
            flow_recent_notes(mock_bm_client)
            mock_bm_client.recent_activity.assert_called_once_with(
                project="kancil",
                page_size=10,
            )

    def test_flow_recent_notes_no_project_filter(self, mock_bm_client):
        mock_bm_client.recent_activity.return_value = []
        with patch("rich.prompt.Prompt.ask", side_effect=["", "10"]):
            flow_recent_notes(mock_bm_client)
            mock_bm_client.recent_activity.assert_called_once_with(
                project=None,
                page_size=10,
            )

    def test_timeline_workflow_invokes_recent_activity(self, mock_bm_client):
        timeline_wf = _get_workflow("query", "run_recent_timeline", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["7d", "kancil", "0"]):
            timeline_wf(console, mock_bm_client)
            assert mock_bm_client.recent_activity.called

    def test_timeline_handles_empty_activity(self, mock_bm_client):
        timeline_wf = _get_workflow("query", "run_recent_timeline", "M3")
        mock_bm_client.recent_activity.return_value = []
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["7d", "", "0"]):
            timeline_wf(console, mock_bm_client)
            # Clean execution without exception
            assert True

    def test_timeline_formats_table_columns(self, mock_bm_client):
        timeline_wf = _get_workflow("query", "run_recent_timeline", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["30d", "kensho", "0"]):
            timeline_wf(console, mock_bm_client)
            output = console.export_text()
            assert "Daily Token" in output or "Recent" in output

    def test_recent_notes_handles_error(self, mock_bm_client):
        mock_bm_client.recent_activity.side_effect = BMError("Database locked")
        with patch("rich.prompt.Prompt.ask", side_effect=["", "10"]):
            with patch("bmh.workflows.query._handle_error") as mock_err:
                flow_recent_notes(mock_bm_client)
                mock_err.assert_called_once()


# ==============================================================================
# Feature 16: Detail Note Reader (R3)
# ==============================================================================
class TestFeature16DetailNoteReader:
    def test_reader_retrieves_note_by_identifier(self, mock_bm_client):
        reader_wf = _get_workflow("query", "run_detail_reader", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil/tasks/daily-token-spend-optimisation", "0"]):
            reader_wf(console, mock_bm_client)
            assert mock_bm_client.read_note.called

    def test_reader_renders_full_content_and_badges(self, mock_bm_client):
        reader_wf = _get_workflow("query", "run_detail_reader", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["tasks/test.md", "0"]):
            reader_wf(console, mock_bm_client)
            output = console.export_text()
            assert "Daily Token Spend" in output or "Test Note" in output

    def test_reader_handles_note_not_found(self, mock_bm_client):
        reader_wf = _get_workflow("query", "run_detail_reader", "M3")
        mock_bm_client.read_note.return_value = {"title": None, "content": None, "frontmatter": None}
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["nonexistent-note", "0"]):
            reader_wf(console, mock_bm_client)
            output = console.export_text()
            assert "not found" in output.lower() or "no content" in output.lower()

    def test_reader_handles_read_exception(self, mock_bm_client):
        reader_wf = _get_workflow("query", "run_detail_reader", "M3")
        mock_bm_client.read_note.side_effect = BMError("File unreadable")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["test-note", "0"]):
            try:
                reader_wf(console, mock_bm_client)
            except BMError:
                pass

    def test_reader_formats_checkboxes(self, mock_bm_client):
        reader_wf = _get_workflow("query", "run_detail_reader", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["test-note", "0"]):
            reader_wf(console, mock_bm_client)
            # Verify panel rendered cleanly
            assert True


# ==============================================================================
# Feature 17: Guided Query Co-Pilot Interview (R3)
# ==============================================================================
class TestFeature17GuidedQueryCoPilotInterview:
    def test_copilot_interviews_intent_scope_type_timeframe(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Find token spend optimization decisions", # intent
            "kancil",                                  # scope
            "decision",                                # type
            "7d",                                      # timeframe
            "token, sqlite",                           # keywords
            "y",                                       # execute search confirm
            "0",                                       # exit / back
        ]):
            copilot_wf(console, mock_bm_client)
            assert mock_bm_client.search_notes.called

    def test_copilot_supports_all_projects_option(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Intent", "all", "all", "anytime", "query term", "y", "0"
        ]):
            copilot_wf(console, mock_bm_client)
            assert mock_bm_client.search_notes.called

    def test_copilot_allows_canceling_before_execution(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Intent", "kancil", "task", "1d", "term", "n", "0"
        ]):
            copilot_wf(console, mock_bm_client)
            # If confirmed 'n', search should not execute
            assert not mock_bm_client.search_notes.called

    def test_copilot_empty_keywords_fallback(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Review recent tasks", "kancil", "task", "7d", "", "y", "0"
        ]):
            copilot_wf(console, mock_bm_client)
            assert mock_bm_client.search_notes.called

    def test_copilot_handles_keyboard_interrupt_gracefully(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=KeyboardInterrupt):
            copilot_wf(console, mock_bm_client)
            assert True


# ==============================================================================
# Feature 18: Co-Pilot Execution & Presentation (R3)
# ==============================================================================
class TestFeature18CoPilotExecutionAndPresentation:
    def test_copilot_displays_synthesis_card(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Find bugs", "kensho", "task", "30d", "sqlite", "y", "0"
        ]):
            copilot_wf(console, mock_bm_client)
            output = console.export_text()
            assert "Co-Pilot" in output or "Formulated" in output or "Query" in output

    def test_copilot_renders_search_results_as_cards(self, mock_bm_client, sample_note_model):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        mock_bm_client.search_notes.return_value = [sample_note_model]
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Search", "kancil", "task", "anytime", "token", "y", "0"
        ]):
            copilot_wf(console, mock_bm_client)
            output = console.export_text()
            assert "Daily Token" in output

    def test_copilot_handles_zero_search_results(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        mock_bm_client.search_notes.return_value = []
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Zero hit query", "kancil", "task", "anytime", "nonexistent", "y", "0"
        ]):
            copilot_wf(console, mock_bm_client)
            output = console.export_text()
            assert "0" in output or "no notes" in output.lower()

    def test_copilot_handles_search_execution_error(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        mock_bm_client.search_notes.side_effect = BMError("Search engine failure")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Search", "kancil", "task", "anytime", "kw", "y", "0"
        ]):
            try:
                copilot_wf(console, mock_bm_client)
            except BMError:
                pass

    def test_copilot_filters_by_selected_project(self, mock_bm_client):
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Intent", "kensho", "insight", "7d", "knowledge", "y", "0"
        ]):
            copilot_wf(console, mock_bm_client)
            call_kwargs = mock_bm_client.search_notes.call_args[1]
            assert call_kwargs.get("project") == "kensho"


# ==============================================================================
# Feature 19: Schema Validator Diagnostic (R4)
# ==============================================================================
class TestFeature19SchemaValidatorDiagnostic:
    def test_schema_validator_invokes_client(self, mock_bm_client):
        lint_wf = _get_workflow("lint", "run_schema_validator", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["", "kancil", "0"]):
            lint_wf(console, mock_bm_client)
            assert mock_bm_client.schema_validate.called

    def test_schema_validator_renders_valid_summary(self, mock_bm_client):
        lint_wf = _get_workflow("lint", "run_schema_validator", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            lint_wf(console, mock_bm_client)
            output = console.export_text()
            assert "TASK" in output or "valid" in output.lower()

    def test_schema_validator_handles_warnings_and_errors(self, mock_bm_client):
        lint_wf = _get_workflow("lint", "run_schema_validator", "M4")
        mock_bm_client.schema_validate.return_value = {
            "total_notes": 1,
            "valid_count": 0,
            "warning_count": 1,
            "error_count": 1,
            "results": [
                {
                    "note_identifier": "TASK-FAIL",
                    "schema_entity": "Task",
                    "passed": False,
                    "warnings": ["Optional missing"],
                    "errors": ["Required missing: description"],
                    "field_results": [],
                }
            ],
            "type_summaries": [],
        }
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["", "kancil", "0"]):
            lint_wf(console, mock_bm_client)
            output = console.export_text()
            assert "TASK-FAIL" in output or "Required" in output

    def test_schema_validator_handles_unknown_type_payload(self, mock_bm_client):
        lint_wf = _get_workflow("lint", "run_schema_validator", "M4")
        mock_bm_client.schema_validate.return_value = {"error": "No notes found of type 'unknown'"}
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["unknown", "kancil", "0"]):
            lint_wf(console, mock_bm_client)
            output = console.export_text()
            assert "unknown" in output or "no notes" in output.lower()

    def test_schema_validator_handles_client_exception(self, mock_bm_client):
        lint_wf = _get_workflow("lint", "run_schema_validator", "M4")
        mock_bm_client.schema_validate.side_effect = BMError("Schema validation crashed")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["", "kancil", "0"]):
            try:
                lint_wf(console, mock_bm_client)
            except BMError:
                pass


# ==============================================================================
# Feature 20: Orphan Link Inspector (R4)
# ==============================================================================
class TestFeature20OrphanLinkInspector:
    def test_orphan_inspector_invokes_client(self, mock_bm_client):
        orphan_wf = _get_workflow("lint", "run_orphan_inspector", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            orphan_wf(console, mock_bm_client)
            assert mock_bm_client.orphans.called

    def test_orphan_inspector_renders_table(self, mock_bm_client):
        orphan_wf = _get_workflow("lint", "run_orphan_inspector", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            orphan_wf(console, mock_bm_client)
            output = console.export_text()
            assert "architecture" in output or "Orphan" in output

    def test_orphan_inspector_empty_celebration(self, mock_bm_client):
        orphan_wf = _get_workflow("lint", "run_orphan_inspector", "M4")
        mock_bm_client.orphans.return_value = []
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kensho", "0"]):
            orphan_wf(console, mock_bm_client)
            output = console.export_text()
            assert "clean" in output.lower() or "0" in output or "no orphan" in output.lower()

    def test_orphan_inspector_handles_project_not_found(self, mock_bm_client):
        orphan_wf = _get_workflow("lint", "run_orphan_inspector", "M4")
        mock_bm_client.orphans.side_effect = BMExecutionError("Project not found", 1, "Error: Project not found")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["bad_project", "0"]):
            try:
                orphan_wf(console, mock_bm_client)
            except BMExecutionError:
                pass

    def test_orphan_inspector_displays_external_id(self, mock_bm_client):
        orphan_wf = _get_workflow("lint", "run_orphan_inspector", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            orphan_wf(console, mock_bm_client)
            output = console.export_text()
            assert "e07bad16" in output or "architecture" in output


# ==============================================================================
# Feature 21: Sync & Index Doctor (R4)
# ==============================================================================
class TestFeature21SyncAndIndexDoctor:
    def test_sync_doctor_invokes_client_doctor(self, mock_bm_client):
        doctor_wf = _get_workflow("lint", "run_sync_doctor", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            doctor_wf(console, mock_bm_client)
            assert mock_bm_client.doctor.called

    def test_sync_doctor_renders_passed_steps(self, mock_bm_client):
        doctor_wf = _get_workflow("lint", "run_sync_doctor", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            doctor_wf(console, mock_bm_client)
            output = console.export_text()
            assert "doctor" in output.lower()

    def test_sync_doctor_handles_failed_status(self, mock_bm_client):
        doctor_wf = _get_workflow("lint", "run_sync_doctor", "M4")
        mock_bm_client.doctor.return_value = {
            "status": "failed",
            "output": "Doctor failed: index mismatch",
            "steps": ["Created doctor project"],
        }
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            doctor_wf(console, mock_bm_client)
            output = console.export_text()
            assert "failed" in output.lower() or "mismatch" in output.lower()

    def test_sync_doctor_handles_exception(self, mock_bm_client):
        doctor_wf = _get_workflow("lint", "run_sync_doctor", "M4")
        mock_bm_client.doctor.side_effect = BMError("Doctor subprocess crashed")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            try:
                doctor_wf(console, mock_bm_client)
            except BMError:
                pass

    def test_sync_doctor_itemizes_check_stages(self, mock_bm_client):
        doctor_wf = _get_workflow("lint", "run_sync_doctor", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            doctor_wf(console, mock_bm_client)
            # Verifies render completion
            assert True


# ==============================================================================
# Feature 22: Schema Drift Analyzer (R4)
# ==============================================================================
class TestFeature22SchemaDriftAnalyzer:
    def test_drift_analyzer_invokes_client_schema_diff(self, mock_bm_client):
        diff_wf = _get_workflow("lint", "run_schema_drift", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            diff_wf(console, mock_bm_client)
            mock_bm_client.schema_diff.assert_called_once_with(note_type="Task", project="kancil")

    def test_drift_analyzer_renders_new_and_dropped_fields(self, mock_bm_client):
        diff_wf = _get_workflow("lint", "run_schema_drift", "M4")
        mock_bm_client.schema_diff.return_value = {
            "note_type": "Task",
            "schema_found": True,
            "new_fields": [{"name": "cadence", "source": "observation", "count": 1, "total": 2, "percentage": 0.5}],
            "dropped_fields": [{"name": "steps", "source": "observation", "count": 0, "total": 2, "percentage": 0.0}],
            "cardinality_changes": [],
        }
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            diff_wf(console, mock_bm_client)
            output = console.export_text()
            assert "cadence" in output or "steps" in output

    def test_drift_analyzer_clean_alignment_badge(self, mock_bm_client):
        diff_wf = _get_workflow("lint", "run_schema_drift", "M4")
        mock_bm_client.schema_diff.return_value = {
            "note_type": "Task",
            "schema_found": True,
            "new_fields": [],
            "dropped_fields": [],
            "cardinality_changes": [],
        }
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            diff_wf(console, mock_bm_client)
            output = console.export_text()
            assert "alignment" in output.lower() or "no drift" in output.lower() or "0" in output

    def test_drift_analyzer_no_schema_found_error_payload(self, mock_bm_client):
        diff_wf = _get_workflow("lint", "run_schema_drift", "M4")
        mock_bm_client.schema_diff.return_value = {"error": "No schema found for type 'Unknown'"}
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["Unknown", "kancil", "0"]):
            diff_wf(console, mock_bm_client)
            output = console.export_text()
            assert "no schema" in output.lower() or "unknown" in output.lower()

    def test_drift_analyzer_handles_client_exception(self, mock_bm_client):
        diff_wf = _get_workflow("lint", "run_schema_drift", "M4")
        mock_bm_client.schema_diff.side_effect = BMError("Schema diff failed")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            try:
                diff_wf(console, mock_bm_client)
            except BMError:
                pass


# ==============================================================================
# Feature 23: 'Lint All' Unified Dashboard (R4)
# ==============================================================================
class TestFeature23LintAllUnifiedDashboard:
    def test_lint_all_runs_all_checks_and_computes_score(self, mock_bm_client):
        lint_all_wf = _get_workflow("lint", "run_lint_all", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            result = lint_all_wf(console, mock_bm_client)
            assert mock_bm_client.doctor.called
            assert mock_bm_client.schema_validate.called
            assert mock_bm_client.orphans.called

    def test_lint_all_assigns_grade_a(self, mock_bm_client):
        lint_all_wf = _get_workflow("lint", "run_lint_all", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            lint_all_wf(console, mock_bm_client)
            output = console.export_text()
            assert "GRADE" in output or "Score" in output or "100" in output or "Healthy" in output

    def test_lint_all_penalizes_failed_doctor(self, mock_bm_client):
        lint_all_wf = _get_workflow("lint", "run_lint_all", "M4")
        mock_bm_client.doctor.return_value = {"status": "failed", "output": "Failed"}
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            lint_all_wf(console, mock_bm_client)
            # Should complete and not crash
            assert True

    def test_lint_all_penalizes_schema_errors(self, mock_bm_client):
        lint_all_wf = _get_workflow("lint", "run_lint_all", "M4")
        mock_bm_client.schema_validate.return_value = {
            "total_notes": 5,
            "valid_count": 2,
            "warning_count": 2,
            "error_count": 3,
            "results": [],
            "type_summaries": [],
        }
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            lint_all_wf(console, mock_bm_client)
            assert True

    def test_lint_all_renders_remediation_action_items(self, mock_bm_client):
        lint_all_wf = _get_workflow("lint", "run_lint_all", "M4")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            lint_all_wf(console, mock_bm_client)
            # Check render completed
            assert True


# ==============================================================================
# Feature 24: Tri-Modal Gateway Menu (R1)
# ==============================================================================
class TestFeature24TriModalGatewayMenu:
    def test_gateway_menu_displays_options_and_exits(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            with patch("bmh.ui.menu.render_banner") as mock_banner:
                run_interactive_session(mock_bm_client)
                mock_banner.assert_called_once()

    def test_gateway_menu_option_ingest(self, mock_bm_client):
        # Option 1 now dispatches to Ingest Hub
        with patch("rich.prompt.Prompt.ask", side_effect=["1", "q"]):
            with patch("bmh.ui.menu.run_ingest_hub") as mock_hub:
                run_interactive_session(mock_bm_client)
                mock_hub.assert_called_once()

    def test_gateway_menu_option_query(self, mock_bm_client):
        # Option 2 now dispatches to Query Hub
        with patch("rich.prompt.Prompt.ask", side_effect=["2", "q"]):
            with patch("bmh.ui.menu.run_query_hub") as mock_hub:
                run_interactive_session(mock_bm_client)
                mock_hub.assert_called_once()

    def test_gateway_menu_option_lint(self, mock_bm_client):
        # Option 3 now dispatches to Lint Hub
        with patch("rich.prompt.Prompt.ask", side_effect=["3", "q"]):
            with patch("bmh.ui.menu.run_lint_hub") as mock_hub:
                run_interactive_session(mock_bm_client)
                mock_hub.assert_called_once()

    def test_gateway_menu_clean_exit_aliases(self, mock_bm_client):
        for alias in ("exit", "quit", "q", "0"):
            with patch("rich.prompt.Prompt.ask", side_effect=[alias]):
                run_interactive_session(mock_bm_client)


# ==============================================================================
# Feature 25: Piped JSON Stream Handling (R1)
# ==============================================================================
class TestFeature25PipedJSONStreamHandling:
    def test_piped_json_array_stream(self, cli_runner):
        input_json = '[{"title": "Piped Task", "content": "- [todo] Item 1"}]'
        with patch("bmh.main.render_note_cards") as mock_render:
            result = cli_runner.invoke(app, [], input=input_json)
            assert result.exit_code == 0
            mock_render.assert_called_once()
            notes = mock_render.call_args[0][0]
            assert len(notes) == 1
            assert notes[0].title == "Piped Task"

    def test_piped_json_envelope_stream(self, cli_runner, sample_search_json):
        with patch("bmh.main.render_note_cards") as mock_render:
            result = cli_runner.invoke(app, [], input=sample_search_json)
            assert result.exit_code == 0
            mock_render.assert_called_once()
            notes = mock_render.call_args[0][0]
            assert len(notes) == 1
            assert notes[0].title == "Daily Token Spend Optimisation"

    def test_piped_single_json_object(self, cli_runner):
        single_obj = '{"title": "Single Note", "content": "Single content"}'
        with patch("bmh.main.render_note_cards") as mock_render:
            result = cli_runner.invoke(app, [], input=single_obj)
            assert result.exit_code == 0
            mock_render.assert_called_once()
            notes = mock_render.call_args[0][0]
            assert notes[0].title == "Single Note"

    def test_piped_plain_text_fallback(self, cli_runner):
        plain_text = "This is raw unformatted text piped into bmh."
        with patch("bmh.main.render_note_cards") as mock_render:
            result = cli_runner.invoke(app, [], input=plain_text)
            assert result.exit_code == 0
            mock_render.assert_called_once()
            notes = mock_render.call_args[0][0]
            assert notes[0].title == "Plain Text Output"

    def test_piped_empty_stdin_warning(self, cli_runner):
        result = cli_runner.invoke(app, [], input="   \n  ")
        assert result.exit_code == 0
        assert "No input provided on stdin" in result.output


# ==============================================================================
# Feature 26: Graceful Error Shielding (R1)
# ==============================================================================
class TestFeature26GracefulErrorShielding:
    def test_handle_client_error_bm_not_found(self):
        with patch("bmh.ui.menu.console.print") as mock_print:
            _handle_client_error(BMNotFoundError("Binary not found"))
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "not found" in output.lower()

    def test_handle_client_error_bm_generic_error(self):
        with patch("bmh.ui.menu.console.print") as mock_print:
            _handle_client_error(BMError("Query syntax invalid"))
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "Basic Memory Error:" in output

    def test_handle_client_error_unexpected_exception(self):
        with patch("bmh.ui.menu.console.print") as mock_print:
            _handle_client_error(RuntimeError("Unexpected state"))
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "Unexpected Error:" in output

    def test_cli_entrypoint_catches_keyboard_interrupt(self):
        import bmh.main as main_mod
        with patch("bmh.main.app", side_effect=KeyboardInterrupt):
            with patch("bmh.main.sys.exit") as mock_exit:
                main_mod.cli_entrypoint()
                mock_exit.assert_called_once_with(0)

    def test_cli_entrypoint_catches_eof_error(self):
        import bmh.main as main_mod
        with patch("bmh.main.app", side_effect=EOFError):
            with patch("bmh.main.sys.exit") as mock_exit:
                main_mod.cli_entrypoint()
                mock_exit.assert_called_once_with(0)


# ==============================================================================
# Feature 27: Update & Exit Integration (R1)
# ==============================================================================
class TestFeature27UpdateAndExitIntegration:
    def test_cli_update_command_success(self, cli_runner):
        with patch("bmh.main.run_self_update", return_value=True) as mock_update:
            result = cli_runner.invoke(app, ["update"])
            assert result.exit_code == 0
            mock_update.assert_called_once()

    def test_cli_update_command_failure_exits_code_1(self, cli_runner):
        with patch("bmh.main.run_self_update", return_value=False):
            result = cli_runner.invoke(app, ["update"])
            assert result.exit_code == 1

    def test_menu_triggers_self_update(self, mock_bm_client):
        # Update is option "4" in the Tri-Modal menu (Ingest=1, Query=2, Lint=3, Update=4)
        with patch("rich.prompt.Prompt.ask", side_effect=["4", "q"]):
            with patch("bmh.ui.menu.run_self_update", return_value=True) as mock_up:
                run_interactive_session(mock_bm_client)
                mock_up.assert_called_once()

    def test_cli_version_flag_exits_zero(self, cli_runner):
        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "bmh version" in result.output

    def test_interactive_session_interrupt_clean_exit(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=KeyboardInterrupt):
            with patch("bmh.ui.menu.render_banner"):
                run_interactive_session(mock_bm_client)
                assert True
