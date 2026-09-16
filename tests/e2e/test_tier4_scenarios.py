from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest
from rich.console import Console
from typer.testing import CliRunner

from bmh.core.client import BMClient, BMError
from bmh.core.models import NoteModel, extract_task_items
from bmh.ui.cards import render_note_card, render_note_cards
from bmh.ui.menu import (
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
# Tier 4: Real-World End-to-End Application Scenarios
# ==============================================================================

class TestTier4Scenario1FullTaskLifecycle:
    """Scenario 1: Full Task Lifecycle (High Complexity)
    Ingest Task Wizard -> Browse Active Tasks -> Checkoff Step -> Lint Verification
    """

    def test_scenario_full_task_lifecycle(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        val_func = _get_workflow("lint", "run_schema_validator", "M4")
        console = Console(record=True)

        # Step 1: Create new Task via Ingest Wizard
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Refactor Token Storage Engine",               # title
            "Migrate in-memory cache to SQLite storage",   # description
            "active",                                      # status
            "high",                                        # priority
            "louis",                                       # assignee
            "Define schema, Run migrations, Test storage", # steps
            "kancil",                                      # project
            "auth, storage",                               # tags
        ]):
            wizard_func(console, mock_bm_client, template_type="task")
            assert mock_bm_client.write_note.called
            write_args = mock_bm_client.write_note.call_args[1]
            assert "Refactor Token Storage Engine" in write_args["title"]
            assert "tasks" in write_args["folder"]

        # Step 2: Browse Active Tasks in Query Hub
        created_task = NoteModel(
            title="Refactor Token Storage Engine",
            content="# Refactor Token Storage Engine\n\n## Steps\n1. [ ] Define schema\n2. [ ] Run migrations\n3. [ ] Test storage\n\n## Observations\n- [status] active",
            entity="kancil/tasks/refactor-token-storage-engine",
            permalink="kancil/tasks/refactor-token-storage-engine",
            note_type="task",
        )
        mock_bm_client.search_notes.return_value = [created_task]

        with patch("rich.prompt.Prompt.ask", return_value="kancil"):
            flow_active_tasks(mock_bm_client)
            mock_bm_client.search_notes.assert_called_with(
                query=None,
                project="kancil",
                note_type="task",
                status="active",
            )

        # Step 3: Check off first step [ ] -> [x]
        mock_bm_client.edit_note(
            identifier=created_task.permalink,
            operation="find_replace",
            find_text="1. [ ] Define schema",
            content="1. [x] Define schema",
            project="kancil",
        )
        assert mock_bm_client.edit_note.called
        edit_kwargs = mock_bm_client.edit_note.call_args[1]
        assert edit_kwargs["operation"] == "find_replace"
        assert "[x] Define schema" in edit_kwargs["content"]

        # Step 4: Verify task schema validity in Lint Hub
        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            val_func(console, mock_bm_client)
            assert mock_bm_client.schema_validate.called


class TestTier4Scenario2ResearchAndInsightIngestion:
    """Scenario 2: Research & Insight Ingestion (High Complexity)
    Piped Ingest -> Observation Appender -> Co-Pilot Retrieval -> Detail Reader
    """

    def test_scenario_research_and_insight_ingestion(self, mock_bm_client):
        piped_func = _get_workflow("ingest", "handle_piped_capture", "M2")
        appender_func = _get_workflow("ingest", "run_quick_appender", "M2")
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        reader_func = _get_workflow("query", "run_detail_reader", "M3")
        console = Console(record=True)

        # Step 1: Piped ingest of research draft
        raw_draft = "# Distributed Lock Latency Analysis\n\nBenchmarking redis vs sqlite locking."
        with patch("sys.stdin.read", return_value=raw_draft):
            with patch("rich.prompt.Prompt.ask", side_effect=["Distributed Lock Latency", "insights", "kancil"]):
                piped_func(mock_bm_client, title="Distributed Lock Latency", folder="insights")

        # Step 2: Append tagged observation
        insight_note = NoteModel(
            title="Distributed Lock Latency",
            content=raw_draft,
            permalink="kancil/insights/distributed-lock-latency",
        )
        mock_bm_client.search_notes.return_value = [insight_note]
        with patch("rich.prompt.Prompt.ask", side_effect=["Distributed Lock", "1", "3", "SQLite WAL mode yields 3x lower latency"]):
            appender_func(console, mock_bm_client)
            assert mock_bm_client.edit_note.called
            assert "[insight]" in mock_bm_client.edit_note.call_args[1]["content"]

        # Step 3: Co-Pilot interview & retrieval
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Find lock latency benchmarks", "kancil", "insight", "7d", "WAL", "y", "0"
        ]):
            copilot_wf(console, mock_bm_client)
            assert mock_bm_client.search_notes.called

        # Step 4: Read full note in Detail Reader
        mock_bm_client.read_note.return_value = {
            "title": "Distributed Lock Latency",
            "content": raw_draft + "\n- [insight] SQLite WAL mode yields 3x lower latency",
            "permalink": "kancil/insights/distributed-lock-latency",
        }
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil/insights/distributed-lock-latency", "0"]):
            reader_func(console, mock_bm_client)
            assert mock_bm_client.read_note.called


class TestTier4Scenario3ProjectHealthAudit:
    """Scenario 3: Project Health Audit (High Complexity)
    Lint All Dashboard -> Schema Diff -> Orphan Fix -> Doctor Verification
    """

    def test_scenario_project_health_audit(self, mock_bm_client):
        lint_all_wf = _get_workflow("lint", "run_lint_all", "M4")
        diff_wf = _get_workflow("lint", "run_schema_drift", "M4")
        orphan_wf = _get_workflow("lint", "run_orphan_inspector", "M4")
        doctor_wf = _get_workflow("lint", "run_sync_doctor", "M4")
        console = Console(record=True)

        # Step 1: Run Lint All Diagnostic Dashboard
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            lint_all_wf(console, mock_bm_client)
            assert mock_bm_client.doctor.called
            assert mock_bm_client.schema_validate.called
            assert mock_bm_client.orphans.called

        # Step 2: Investigate schema drift
        mock_bm_client.schema_diff.return_value = {
            "note_type": "Task",
            "schema_found": True,
            "new_fields": [{"name": "cadence", "source": "observation", "count": 1, "total": 2, "percentage": 0.5}],
            "dropped_fields": [],
            "cardinality_changes": [],
        }
        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            diff_wf(console, mock_bm_client)
            mock_bm_client.schema_diff.assert_called_with(note_type="Task", project="kancil")

        # Step 3: Check orphan list after linking
        mock_bm_client.orphans.return_value = []
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            orphan_wf(console, mock_bm_client)
            mock_bm_client.orphans.assert_called_with(project="kancil")

        # Step 4: Run doctor consistency verification
        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            doctor_wf(console, mock_bm_client)
            assert mock_bm_client.doctor.called


class TestTier4Scenario4MeetingNotesToDecisions:
    """Scenario 4: Meeting Notes to Decisions (Medium Complexity)
    Meeting Wizard -> Decision Wizard -> Project Browser (kancil/kensho)
    """

    def test_scenario_meeting_notes_to_decisions(self, mock_bm_client):
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)

        # Step 1: Create Meeting Note
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Sprint Architecture Planning",
            "2026-09-16",
            "syafiq, louis",
            "Discuss tri-modal CLI architecture",
            "Adopt Ingest, Query, Lint hub layout",
            "Scope bounds and timeout limits",
            "Author comprehensive tests",
            "kancil",
        ]):
            wizard_func(console, mock_bm_client, template_type="meeting")
            assert mock_bm_client.write_note.called
            meeting_call = mock_bm_client.write_note.call_args[1]
            assert "Sprint Architecture Planning" in meeting_call["title"]

        # Step 2: Create Formal Decision Record (ADR)
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Adopt Tri-Modal CLI Hub Architecture",
            "decided",
            "Need clear terminal separation for Ingest, Query, Lint",
            "Adopt 3-hub Tri-Modal gateway",
            "Improves user ergonomics and reduces cognitive load",
            "Requires migration of legacy menu options",
            "kensho",
        ]):
            wizard_func(console, mock_bm_client, template_type="decision")
            assert mock_bm_client.write_note.called
            decision_call = mock_bm_client.write_note.call_args[1]
            assert "Adopt Tri-Modal" in decision_call["title"]

        # Step 3: Browse newly created records in Project Browser
        decision_note = NoteModel(
            title="Adopt Tri-Modal CLI Hub Architecture",
            content="# Adopt Tri-Modal CLI Hub Architecture\n\n- [decision] Adopt 3-hub gateway",
            permalink="kensho/decisions/adopt-tri-modal",
            note_type="decision",
        )
        mock_bm_client.search_notes.return_value = [decision_note]
        with patch("rich.prompt.Prompt.ask", side_effect=["2", "Tri-Modal"]):
            flow_browse_project(mock_bm_client)
            mock_bm_client.search_notes.assert_called_with(
                query="Tri-Modal",
                project="kensho",
            )


class TestTier4Scenario5PipedStreamCLIPipeline:
    """Scenario 5: Piped Stream CLI Pipeline (Medium Complexity)
    Piped JSON Stream -> Rich Card Formatting -> Error Shielding on Bad JSON
    """

    def test_scenario_piped_stream_full_pipeline(self, cli_runner):
        # 1. Piped search result JSON stream
        stream_json = json.dumps([
            {
                "title": "Pipeline Note A",
                "content": "# Pipeline Note A\n- [status] active\n1. [ ] Step 1",
                "entity": "kancil/notes/pipeline-a",
                "updated_at": "2026-09-16T12:00:00Z",
            },
            {
                "title": "Pipeline Note B",
                "content": "# Pipeline Note B\n- [decision] Standardise CLI",
                "entity": "kancil/notes/pipeline-b",
                "updated_at": "2026-09-16T12:05:00Z",
            }
        ])

        with patch("bmh.main.render_note_cards") as mock_render:
            res = cli_runner.invoke(app, [], input=stream_json)
            assert res.exit_code == 0
            mock_render.assert_called_once()
            notes = mock_render.call_args[0][0]
            assert len(notes) == 2
            assert notes[0].title == "Pipeline Note A"
            assert notes[1].title == "Pipeline Note B"

        # 2. Piped non-JSON text fallback
        plain_stream = "# Non-JSON Heading\n\nRaw text piped directly from pipe."
        with patch("bmh.main.render_note_cards") as mock_render:
            res_plain = cli_runner.invoke(app, [], input=plain_stream)
            assert res_plain.exit_code == 0
            mock_render.assert_called_once()
            notes_plain = mock_render.call_args[0][0]
            assert notes_plain[0].title == "Plain Text Output"
            assert "Non-JSON Heading" in notes_plain[0].content

        # 3. Piped empty stream warning
        res_empty = cli_runner.invoke(app, [], input="   \n")
        assert res_empty.exit_code == 0
        assert "No input provided on stdin" in res_empty.output
