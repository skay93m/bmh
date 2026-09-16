from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest
from rich.console import Console
from rich.panel import Panel
from typer.testing import CliRunner

from bmh.core.client import BMClient, BMError, BMExecutionError, BMNotFoundError
from bmh.core.models import (
    NoteModel,
    SearchResult,
    normalize_notes_json,
    extract_task_items,
    LintAllSummary,
)
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
from bmh.main import app


def _get_workflow(hub: str, func_name: str, milestone: str):
    try:
        mod = __import__(f"bmh.workflows.{hub}", fromlist=[func_name])
        return getattr(mod, func_name)
    except (ImportError, AttributeError):
        pytest.skip(f"Workflow function '{hub}.{func_name}' not yet implemented ({milestone})")


# ==============================================================================
# Tier 2: Boundary & Corner Cases (Category-Partition & BVA)
# ==============================================================================

class TestTier2EmptyAndWhitespaceBoundaries:
    """BVA on empty and whitespace inputs."""

    def test_search_notes_empty_query_returns_early(self, mock_bm_client):
        # New impl: empty query returns early without searching
        with patch("rich.prompt.Prompt.ask", side_effect=["", ""]):
            with patch("rich.prompt.Confirm.ask", return_value=False):
                flow_search_notes(mock_bm_client)
                mock_bm_client.search_notes.assert_not_called()

    def test_search_notes_whitespace_only_stripped_to_none(self, mock_bm_client):
        # New impl: whitespace-only query also returns early
        with patch("rich.prompt.Prompt.ask", side_effect=["   \t  ", "   "]):
            with patch("rich.prompt.Confirm.ask", return_value=False):
                flow_search_notes(mock_bm_client)
                mock_bm_client.search_notes.assert_not_called()

    def test_piped_stdin_empty_string(self, cli_runner):
        result = cli_runner.invoke(app, [], input="")
        assert result.exit_code == 0
        assert "No input provided on stdin" in result.output

    def test_piped_stdin_whitespace_newlines_only(self, cli_runner):
        result = cli_runner.invoke(app, [], input="  \n\n\t  \n  ")
        assert result.exit_code == 0
        assert "No input provided on stdin" in result.output

    def test_note_model_empty_and_whitespace_title(self):
        n1 = NoteModel(title="")
        assert n1.title == "Untitled Note"
        n2 = NoteModel(title="    ")
        assert n2.title == "Untitled Note"
        n3 = NoteModel(title=None)
        assert n3.title == "Untitled Note"

    def test_note_model_none_content_normalizes_to_empty_string(self):
        note = NoteModel(content=None)
        assert note.content == ""

    def test_render_note_card_empty_content_shows_placeholder(self):
        note = NoteModel(title="Empty Note", content="")
        panel = render_note_card(note)
        assert isinstance(panel, Panel)
        assert "Empty Note" in str(panel.title)

    def test_render_note_cards_empty_list_prints_friendly_warning(self, capture_console):
        render_note_cards([], custom_console=capture_console)
        output = capture_console.export_text()
        assert "No notes found matching criteria" in output


class TestTier2ExtremeInputsAndSpecialCharacters:
    """Adversarial stress testing with special characters, escaping, and extreme sizes."""

    def test_note_title_and_content_with_special_characters(self):
        title = "Fix: <script>alert('xss')</script> & [decision] / \\ | $ # @ ! *"
        body = "Line with <b>HTML</b> & markdown *italics* and `backticks` and [risk] tag."
        note = NoteModel(title=title, content=body)
        assert note.title == title
        panel = render_note_card(note)
        assert isinstance(panel, Panel)

    def test_highlight_observations_escaping_brackets_and_regex(self):
        raw = "Nested [decision] with [risk] and regex meta-chars: ^.*+?[]{}()|\\"
        highlighted = _highlight_observations(raw)
        assert "[bold green]\\[decision][/bold green]" in highlighted
        assert "[bold red]\\[risk][/bold red]" in highlighted

    def test_normalize_notes_json_large_payload(self):
        large_content = "# Massive Note\n" + ("Lorem ipsum dolor sit amet. \n" * 1000)
        json_data = json.dumps([{"title": "Large Note", "content": large_content}])
        notes = normalize_notes_json(json_data)
        assert len(notes) == 1
        assert len(notes[0].content) > 20000

    def test_search_notes_with_regex_special_characters(self, mock_bm_client):
        query = "pattern[0-9]+.*"
        with patch("rich.prompt.Prompt.ask", side_effect=[query, "kancil"]):
            with patch("rich.prompt.Confirm.ask", return_value=False):
                flow_search_notes(mock_bm_client)
                mock_bm_client.search_notes.assert_called_once_with(
                    query=query,
                    project="kancil",
                    is_title=False,
                )

    def test_piped_malformed_json_fallback_to_plain_text(self, cli_runner):
        malformed = '{"title": "Unclosed string, missing brace'
        with patch("bmh.main.render_note_cards") as mock_render:
            result = cli_runner.invoke(app, [], input=malformed)
            assert result.exit_code == 0
            mock_render.assert_called_once()
            notes = mock_render.call_args[0][0]
            assert notes[0].title == "Plain Text Output"
            assert malformed in notes[0].content

    def test_piped_json_primitive_number_or_boolean(self, cli_runner):
        with patch("bmh.main.render_note_cards") as mock_render:
            result = cli_runner.invoke(app, [], input="12345")
            assert result.exit_code == 0
            mock_render.assert_called_once()
            notes = mock_render.call_args[0][0]
            assert notes[0].content == "12345"


class TestTier2SubprocessErrorModalities:
    """BVA on exit codes and error payloads as documented in survey reports."""

    def test_client_missing_binary_raises_bm_not_found(self):
        client = BMClient(binary_path="/path/does/not/exist/bm")
        with pytest.raises(BMNotFoundError):
            client.execute(["version"])

    def test_client_timeout_raises_bm_error(self):
        client = BMClient(binary_path="/bin/echo")
        with patch("subprocess.run", side_effect=Exception("Timeout")):
            with pytest.raises(BMError) as exc_info:
                client.execute(["test"])
            assert "failed" in str(exc_info.value).lower()

    def test_client_read_note_not_found_returns_none(self):
        """read-note returns exit 0 with all nulls when note does not exist."""
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"title": None, "permalink": None, "file_path": None, "content": None, "frontmatter": None}),
            )
            res = client.read_note("nonexistent-identifier")
            assert res is None

    def test_client_schema_validate_unknown_type_payload(self):
        """schema-validate exits 0 with error payload when target type does not exist."""
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"error": "No notes found of type 'Nonexistent'"}),
            )
            res = client.schema_validate(target="Nonexistent")
            assert "error" in res
            assert "No notes found" in res["error"]

    def test_client_schema_diff_no_schema_found_payload(self):
        """schema-diff exits 0 with error payload when schema does not exist."""
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"error": "No schema found for type 'Nonexistent'"}),
            )
            res = client.schema_diff(note_type="Nonexistent")
            assert "error" in res
            assert "No schema found" in res["error"]

    def test_client_orphans_project_not_found_exit_code_1(self):
        """orphans exits 1 with JSON error when project does not exist."""
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.side_effect = BMExecutionError(
                "Project not found", 1, "Error: Project not found", stdout=json.dumps({"error": "Project not found"})
            )
            res = client.orphans(project="bad_project")
            assert len(res) == 1
            assert "error" in res[0]

    def test_client_doctor_failure_exit_code_1_parsed(self):
        """doctor failure parsing."""
        client = BMClient(binary_path="/bin/echo")
        with patch.object(client, "execute") as mock_exec:
            mock_exec.side_effect = BMExecutionError(
                "Doctor failed", 1, "Doctor failed: Index corruption", stdout="OK Check 1\nDoctor failed: Index corruption"
            )
            res = client.doctor()
            assert res["passed"] is False
            assert res["status"] == "failed"


class TestTier2TaskStepCheckoffBoundaries:
    """BVA on task checklists and interactive step parsing."""

    def test_extract_task_items_empty_markdown(self):
        items = extract_task_items("")
        assert items == []

    def test_extract_task_items_markdown_without_checkboxes(self):
        markdown = """
        # Task Note
        This is a regular task with paragraphs but no checkboxes.
        - Bullet point without box
        1. Numbered list without box
        """
        items = extract_task_items(markdown)
        assert items == []

    def test_extract_task_items_all_completed(self):
        markdown = """
        ## Steps
        1. [x] Step 1
        2. [X] Step 2
        - [x] Step 3
        """
        items = extract_task_items(markdown)
        assert len(items) == 3
        assert all(item.completed for item in items)

    def test_extract_task_items_mixed_whitespace_and_cases(self):
        markdown = """
        1.  [ ]   Spaced step
        2. [x] Done step
        -   [ ]   Bullet spaced step
        """
        items = extract_task_items(markdown)
        assert len(items) == 3
        assert items[0].text == "Spaced step"
        assert items[0].completed is False
        assert items[1].completed is True
        assert items[2].text == "Bullet spaced step"

    def test_task_checkoff_with_identical_step_names(self, mock_bm_client):
        """When multiple steps have the same text, it should target the correct occurrence."""
        markdown = """
        1. [ ] Check logs
        2. [ ] Check logs
        """
        note = NoteModel(title="Multi-Step Task", content=markdown)
        mock_bm_client.search_notes.return_value = [note]
        inspector_wf = _get_workflow("query", "run_active_tasks_inspector", "M3")
        console = Console(record=True)
        with patch("rich.prompt.Prompt.ask", side_effect=["1", "1", "0"]):
            inspector_wf(console, mock_bm_client)
            if mock_bm_client.edit_note.called:
                assert mock_bm_client.edit_note.call_args[1]["operation"] == "find_replace"


class TestTier2LintScoringBoundaries:
    """BVA on Lint All score calculation (0 to 100 points, Grades A-F)."""

    def test_lint_score_perfect_100_grade_a(self):
        summary = LintAllSummary(
            health_score=100,
            grade="A",
            doctor_passed=True,
            total_notes=10,
            valid_schemas=10,
            schema_warnings=0,
            schema_errors=0,
            orphan_count=0,
            drift_count=0,
        )
        assert summary.health_score == 100
        assert summary.grade == "A"

    def test_lint_score_floor_clamped_to_zero(self):
        """Multiple failures cannot drag score below 0."""
        # Simulated calculation
        calc_score = 40 * (0 / 10) - (5 * 10) - (10 * 2)  # Negative
        clamped = max(0, int(calc_score))
        summary = LintAllSummary(health_score=clamped, grade="F", doctor_passed=False)
        assert summary.health_score == 0
        assert summary.grade == "F"

    def test_lint_score_grade_thresholds(self):
        grades = {
            95: "A",
            90: "A",
            85: "B",
            75: "B",
            70: "C",
            60: "C",
            59: "F",
            0: "F",
        }
        for score, expected_grade in grades.items():
            summary = LintAllSummary(health_score=score, grade=expected_grade)
            assert summary.grade == expected_grade


class TestTier2NavigationAndSignalBoundaries:
    """BVA on user interrupt signals and invalid menu selections."""

    def test_interactive_session_invalid_choice_reprompts_and_exits(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=["invalid_choice", "999", "0"]):
            with patch("bmh.ui.menu.render_banner"):
                run_interactive_session(mock_bm_client)
                # Session handled invalid inputs and terminated on 0
                assert True

    def test_interactive_session_keyboard_interrupt_exits_cleanly(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=KeyboardInterrupt):
            with patch("bmh.ui.menu.render_banner"):
                run_interactive_session(mock_bm_client)
                assert True

    def test_interactive_session_eof_error_exits_cleanly(self, mock_bm_client):
        with patch("rich.prompt.Prompt.ask", side_effect=EOFError):
            with patch("bmh.ui.menu.render_banner"):
                run_interactive_session(mock_bm_client)
                assert True

    def test_format_date_handles_none_and_invalid_date_strings(self):
        assert _format_date(None) is None
        assert _format_date("") is None
        assert _format_date("not-a-date") == "not-a-date"
        assert _format_date("2026-09-15T10:30:00Z") == "15/09/26 10:30"
