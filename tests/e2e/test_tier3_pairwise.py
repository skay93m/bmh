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


def _get_workflow(hub: str, func_name: str, milestone: str):
    try:
        mod = __import__(f"bmh.workflows.{hub}", fromlist=[func_name])
        return getattr(mod, func_name)
    except (ImportError, AttributeError):
        pytest.skip(f"Workflow function '{hub}.{func_name}' not yet implemented ({milestone})")


# ==============================================================================
# Tier 3: Pairwise Cross-Hub Combinatorial Interactions
# ==============================================================================

class TestTier3PairwiseIngestAndQuery:
    """Pairwise interactions between Ingest Hub (M2) and Query Hub (M3)."""

    def test_pair_task_ingest_then_query_search(self, mock_bm_client):
        """Ingest Task Wizard -> Browse in Search Notes."""
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)

        # 1. Ingest task note
        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Pairwise Task", "Task description", "active", "high", "louis", "Step 1", "kancil", "auth"
        ]):
            wizard_func(console, mock_bm_client, template_type="task")

        # 2. Query search
        created_note = NoteModel(
            title="Pairwise Task",
            content="# Pairwise Task\n\n## Steps\n1. [ ] Step 1\n\n## Observations\n- [status] active",
            entity="kancil/tasks/pairwise-task",
            note_type="task",
        )
        mock_bm_client.search_notes.return_value = [created_note]
        with patch("rich.prompt.Prompt.ask", side_effect=["Pairwise Task", "kancil"]):
            with patch("rich.prompt.Confirm.ask", return_value=False):
                flow_search_notes(mock_bm_client)
                mock_bm_client.search_notes.assert_called_with(
                    query="Pairwise Task",
                    project="kancil",
                    is_title=False,
                )

    def test_pair_piped_ingest_then_detail_reader(self, mock_bm_client):
        """Piped Ingest Handler -> Inspect in Detail Note Reader."""
        piped_func = _get_workflow("ingest", "handle_piped_capture", "M2")
        reader_func = _get_workflow("query", "run_detail_reader", "M3")
        console = Console(record=True)

        raw_md = "# Piped Architecture\n\n- [insight] Cache invalidation latency."
        with patch("sys.stdin.read", return_value=raw_md):
            with patch("rich.prompt.Prompt.ask", side_effect=["Piped Architecture", "insights", "kensho"]):
                piped_func(mock_bm_client, title="Piped Architecture", folder="insights")

        mock_bm_client.read_note.return_value = {
            "title": "Piped Architecture",
            "content": raw_md,
            "permalink": "kensho/insights/piped-architecture",
        }
        with patch("rich.prompt.Prompt.ask", side_effect=["kensho/insights/piped-architecture", "0"]):
            reader_func(console, mock_bm_client)
            assert mock_bm_client.read_note.called

    def test_pair_query_search_then_quick_observation_appender(self, mock_bm_client, sample_note_model):
        """Search note in Query -> Append observation via Quick Appender."""
        appender_func = _get_workflow("ingest", "run_quick_appender", "M2")
        console = Console(record=True)

        mock_bm_client.search_notes.return_value = [sample_note_model]
        with patch("rich.prompt.Prompt.ask", side_effect=["Daily Token", "1", "1", "Approved scaling plan"]):
            appender_func(console, mock_bm_client)
            assert mock_bm_client.edit_note.called
            call_kwargs = mock_bm_client.edit_note.call_args[1]
            assert "[decision]" in call_kwargs["content"]

    def test_pair_insight_ingest_in_kensho_then_project_browser(self, mock_bm_client):
        """Ingest Insight in 'kensho' -> Browse 'kensho' in Project Browser."""
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)

        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Kensho Research", "Finding", "Takeaway", "Impact", "durable", "kensho"
        ]):
            wizard_func(console, mock_bm_client, template_type="insight")

        with patch("rich.prompt.Prompt.ask", side_effect=["2", "Research"]):
            flow_browse_project(mock_bm_client)
            mock_bm_client.search_notes.assert_called_with(
                query="Research",
                project="kensho",
            )

    def test_pair_meeting_ingest_then_active_tasks(self, mock_bm_client):
        """Ingest Meeting with Action Items -> Inspect Active Tasks."""
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        console = Console(record=True)

        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Q3 Review", "2026-09-16", "team", "Agenda", "Dec", "Risk", "Review pull request", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="meeting")

        with patch("rich.prompt.Prompt.ask", return_value="kancil"):
            flow_active_tasks(mock_bm_client)
            mock_bm_client.search_notes.assert_called_with(
                query=None,
                project="kancil",
                note_type="task",
                status="active",
            )


class TestTier3PairwiseQueryAndLint:
    """Pairwise interactions between Query Hub (M3) and Lint Hub (M4)."""

    def test_pair_active_task_step_checkoff_then_schema_validate(self, mock_bm_client, sample_note_model):
        """Active task step checkoff -> Schema validate task note."""
        val_func = _get_workflow("lint", "run_schema_validator", "M4")
        console = Console(record=True)

        # 1. Step checkoff
        mock_bm_client.edit_note(
            identifier=sample_note_model.permalink or sample_note_model.title,
            operation="find_replace",
            find_text="1. [ ] Baseline measurement",
            content="1. [x] Baseline measurement",
        )
        assert mock_bm_client.edit_note.called

        # 2. Schema validate
        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            val_func(console, mock_bm_client)
            assert mock_bm_client.schema_validate.called

    def test_pair_project_browser_discovery_then_orphan_inspector(self, mock_bm_client):
        """Project browser discovers unlinked entity -> Verify in Orphan Inspector."""
        orphan_func = _get_workflow("lint", "run_orphan_inspector", "M4")
        console = Console(record=True)

        # Browse project
        with patch("rich.prompt.Prompt.ask", side_effect=["1", "architecture"]):
            flow_browse_project(mock_bm_client)

        # Check orphans
        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            orphan_func(console, mock_bm_client)
            mock_bm_client.orphans.assert_called_with(project="kancil")

    def test_pair_copilot_retrieves_note_then_schema_diff(self, mock_bm_client):
        """Co-Pilot retrieves note -> Schema drift analyzer inspects drift."""
        copilot_wf = _get_workflow("query", "run_guided_copilot", "M3")
        diff_wf = _get_workflow("lint", "run_schema_drift", "M4")
        console = Console(record=True)

        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Find task schemas", "kancil", "task", "anytime", "task", "y", "0"
        ]):
            copilot_wf(console, mock_bm_client)

        with patch("rich.prompt.Prompt.ask", side_effect=["Task", "kancil", "0"]):
            diff_wf(console, mock_bm_client)
            mock_bm_client.schema_diff.assert_called_with(note_type="Task", project="kancil")

    def test_pair_recent_activity_then_sync_doctor(self, mock_bm_client):
        """Recent activity timeline -> Verify local SQLite consistency via Doctor."""
        doctor_wf = _get_workflow("lint", "run_sync_doctor", "M4")
        console = Console(record=True)

        with patch("rich.prompt.Prompt.ask", return_value="kancil"):
            flow_recent_notes(mock_bm_client)

        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            doctor_wf(console, mock_bm_client)
            assert mock_bm_client.doctor.called


class TestTier3PairwiseIngestAndLint:
    """Pairwise interactions between Ingest Hub (M2) and Lint Hub (M4)."""

    def test_pair_decision_ingest_then_schema_validate(self, mock_bm_client):
        """Ingest Decision Note -> Schema validate decision notes."""
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        val_func = _get_workflow("lint", "run_schema_validator", "M4")
        console = Console(record=True)

        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Adopt Pydantic v2", "decided", "Need typed contracts", "Adopted", "High perf", "None", "kensho"
        ]):
            wizard_func(console, mock_bm_client, template_type="decision")

        with patch("rich.prompt.Prompt.ask", side_effect=["Decision", "kensho", "0"]):
            val_func(console, mock_bm_client)
            mock_bm_client.schema_validate.assert_called_with(target="Decision", project="kensho")

    def test_pair_piped_capture_then_doctor_verification(self, mock_bm_client):
        """Piped Ingest raw markdown -> Doctor verifies indexing health."""
        piped_func = _get_workflow("ingest", "handle_piped_capture", "M2")
        doctor_wf = _get_workflow("lint", "run_sync_doctor", "M4")
        console = Console(record=True)

        with patch("sys.stdin.read", return_value="# Ingested Raw Notes\n"):
            with patch("rich.prompt.Prompt.ask", side_effect=["Ingested Notes", "inbox", "kancil"]):
                piped_func(mock_bm_client, title="Ingested Notes", folder="inbox")

        with patch("rich.prompt.Prompt.ask", side_effect=["0"]):
            doctor_wf(console, mock_bm_client)
            assert mock_bm_client.doctor.called

    def test_pair_ingest_note_then_lint_all_dashboard(self, mock_bm_client):
        """Ingest Note -> Run Lint All Dashboard to verify health score."""
        wizard_func = _get_workflow("ingest", "run_note_wizard", "M2")
        lint_all_wf = _get_workflow("lint", "run_lint_all", "M4")
        console = Console(record=True)

        with patch("rich.prompt.Prompt.ask", side_effect=[
            "Temporary Scratch", "Freeform thoughts", "draft", "kancil"
        ]):
            wizard_func(console, mock_bm_client, template_type="scratchpad")

        with patch("rich.prompt.Prompt.ask", side_effect=["kancil", "0"]):
            lint_all_wf(console, mock_bm_client)
            assert mock_bm_client.doctor.called
            assert mock_bm_client.schema_validate.called


class TestTier3PairwiseGatewayAndHubs:
    """Pairwise interactions between Gateway Menu (R1/M5) and all hubs."""

    def test_gateway_navigates_to_ingest_then_exits(self, mock_bm_client):
        """Gateway -> Option 1 Ingest Hub -> Hub exits -> Option 0 Exit."""
        with patch("bmh.ui.menu.run_ingest_hub") as mock_hub:
            with patch("rich.prompt.Prompt.ask", side_effect=["1", "0"]):
                run_interactive_session(mock_bm_client)
                mock_hub.assert_called_once_with(mock_bm_client)

    def test_gateway_navigates_to_query_then_exits(self, mock_bm_client):
        """Gateway -> Option 2 Query Hub -> Hub exits -> Option 0 Exit."""
        with patch("bmh.ui.menu.run_query_hub") as mock_hub:
            with patch("rich.prompt.Prompt.ask", side_effect=["2", "0"]):
                run_interactive_session(mock_bm_client)
                mock_hub.assert_called_once_with(mock_bm_client)

    def test_gateway_navigates_to_lint_then_exits(self, mock_bm_client):
        """Gateway -> Option 3 Lint Hub -> Hub exits -> Option 0 Exit."""
        with patch("bmh.ui.menu.run_lint_hub") as mock_hub:
            with patch("rich.prompt.Prompt.ask", side_effect=["3", "0"]):
                run_interactive_session(mock_bm_client)
                mock_hub.assert_called_once_with(mock_bm_client)

    def test_gateway_navigates_to_update_then_exits(self, mock_bm_client):
        """Gateway -> Option 4 Update -> then Exit."""
        with patch("bmh.ui.menu.run_self_update", return_value=True) as mock_update:
            with patch("rich.prompt.Prompt.ask", side_effect=["4", "0"]):
                run_interactive_session(mock_bm_client)
                mock_update.assert_called_once()
