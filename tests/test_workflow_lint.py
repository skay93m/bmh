from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from bmh.core.client import BMClient, BMError
from bmh.workflows.lint import (
    flow_schema_validate,
    flow_orphan_inspector,
    flow_doctor,
    flow_schema_drift,
    flow_lint_all,
    run_lint_hub,
)


def test_flow_schema_validate_all():
    mock_client = MagicMock(spec=BMClient)
    mock_client.schema_validate.return_value = {
        "total_notes": 10,
        "valid_count": 9,
        "warning_count": 1,
        "error_count": 0,
        "results": [],
    }

    with patch("rich.prompt.Prompt.ask", side_effect=["1", ""]):  # all notes, no project
        with patch("bmh.workflows.lint.render_schema_validation_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_schema_validate(mock_client)
            mock_panel.assert_called_once()

    mock_client.schema_validate.assert_called_once_with(target=None, project=None)


def test_flow_schema_validate_specific_type():
    mock_client = MagicMock(spec=BMClient)
    mock_client.schema_validate.return_value = {
        "total_notes": 5,
        "valid_count": 5,
        "warning_count": 0,
        "error_count": 0,
        "results": [],
    }

    with patch("rich.prompt.Prompt.ask", side_effect=["2", ""]):  # task type
        with patch("bmh.workflows.lint.render_schema_validation_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_schema_validate(mock_client)

    mock_client.schema_validate.assert_called_once_with(target="task", project=None)


def test_flow_schema_validate_error_handled():
    mock_client = MagicMock(spec=BMClient)
    mock_client.schema_validate.side_effect = BMError("Validation failed")

    with patch("rich.prompt.Prompt.ask", side_effect=["1", ""]):
        with patch("bmh.workflows.lint.render_schema_validation_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_schema_validate(mock_client)
            mock_panel.assert_called_once()


def test_flow_orphan_inspector_no_orphans():
    mock_client = MagicMock(spec=BMClient)
    mock_client.orphans.return_value = []

    with patch("rich.prompt.Prompt.ask", return_value=""):
        with patch("bmh.workflows.lint.render_orphan_list_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_orphan_inspector(mock_client)
            mock_panel.assert_called_once_with([])


def test_flow_orphan_inspector_with_orphans():
    mock_client = MagicMock(spec=BMClient)
    mock_client.orphans.return_value = [
        {"title": "Orphan Note", "external_id": "uuid-1", "note_type": "note"},
    ]

    with patch("rich.prompt.Prompt.ask", return_value="kancil"):
        with patch("bmh.workflows.lint.render_orphan_list_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_orphan_inspector(mock_client)
            mock_panel.assert_called_once()

    mock_client.orphans.assert_called_once_with(project="kancil")


def test_flow_orphan_inspector_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.orphans.side_effect = BMError("Orphan check failed")

    with patch("rich.prompt.Prompt.ask", return_value=""):
        with patch("bmh.workflows.lint.render_orphan_list_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_orphan_inspector(mock_client)
            # error case uses error list
            call_args = mock_panel.call_args[0][0]
            assert isinstance(call_args, list)
            assert any("error" in str(item).lower() for item in call_args)


def test_flow_doctor_passed():
    mock_client = MagicMock(spec=BMClient)
    mock_client.doctor.return_value = {
        "passed": True,
        "status": "passed",
        "output": "Doctor checks passed",
        "steps": ["Files indexed", "Search operational"],
    }

    with patch("bmh.workflows.lint.render_doctor_panel") as mock_panel:
        mock_panel.return_value = MagicMock()
        flow_doctor(mock_client)
        mock_panel.assert_called_once()


def test_flow_doctor_failed():
    mock_client = MagicMock(spec=BMClient)
    mock_client.doctor.return_value = {
        "passed": False,
        "status": "failed",
        "output": "Doctor check failed",
        "steps": [],
    }

    with patch("bmh.workflows.lint.render_doctor_panel") as mock_panel:
        mock_panel.return_value = MagicMock()
        flow_doctor(mock_client)
        mock_panel.assert_called_once()


def test_flow_doctor_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.doctor.side_effect = BMError("Doctor failed")

    with patch("bmh.workflows.lint.render_doctor_panel") as mock_panel:
        mock_panel.return_value = MagicMock()
        flow_doctor(mock_client)
        mock_panel.assert_called_once()
        data = mock_panel.call_args[0][0]
        assert data.get("passed") is False


def test_flow_schema_drift_known_type():
    mock_client = MagicMock(spec=BMClient)
    mock_client.schema_diff.return_value = {
        "note_type": "task",
        "schema_found": True,
        "new_fields": [],
        "dropped_fields": [],
        "cardinality_changes": [],
    }

    with patch("rich.prompt.Prompt.ask", side_effect=["1", ""]):  # task type
        with patch("bmh.workflows.lint.render_schema_diff_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_schema_drift(mock_client)
            mock_panel.assert_called_once()

    mock_client.schema_diff.assert_called_once_with(note_type="task", project=None)


def test_flow_schema_drift_custom_type():
    mock_client = MagicMock(spec=BMClient)
    mock_client.schema_diff.return_value = {"note_type": "guide", "schema_found": False}

    custom_idx = str(len(["task", "insight", "meeting", "decision", "note", "spec", "guide", "report"]) + 1)
    with patch("rich.prompt.Prompt.ask", side_effect=[custom_idx, "guide", ""]):
        with patch("bmh.workflows.lint.render_schema_diff_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_schema_drift(mock_client)

    mock_client.schema_diff.assert_called_once_with(note_type="guide", project=None)


def test_flow_schema_drift_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.schema_diff.side_effect = BMError("Drift failed")

    with patch("rich.prompt.Prompt.ask", side_effect=["1", ""]):
        with patch("bmh.workflows.lint.render_schema_diff_panel") as mock_panel:
            mock_panel.return_value = MagicMock()
            flow_schema_drift(mock_client)
            mock_panel.assert_called_once()
            data = mock_panel.call_args[0][0]
            assert "error" in data


def test_flow_lint_all_full():
    mock_client = MagicMock(spec=BMClient)
    mock_client.doctor.return_value = {"passed": True, "status": "passed", "output": "", "steps": []}
    mock_client.schema_validate.return_value = {"total_notes": 10, "valid_count": 10, "warning_count": 0, "error_count": 0}
    mock_client.orphans.return_value = []
    mock_client.schema_diff.return_value = {"note_type": "task", "schema_found": True, "new_fields": [], "dropped_fields": []}

    with patch("rich.prompt.Prompt.ask", side_effect=["", "task"]):
        with patch("bmh.workflows.lint.render_lint_all_dashboard") as mock_dash:
            mock_dash.return_value = MagicMock()
            flow_lint_all(mock_client)
            mock_dash.assert_called_once()

    # Verify all four checks were called
    mock_client.doctor.assert_called_once()
    mock_client.schema_validate.assert_called_once()
    mock_client.orphans.assert_called_once()
    mock_client.schema_diff.assert_called_once_with(note_type="task", project=None)


def test_flow_lint_all_with_errors():
    mock_client = MagicMock(spec=BMClient)
    mock_client.doctor.return_value = {"passed": False, "status": "failed", "output": "Failed", "steps": []}
    mock_client.schema_validate.return_value = {"total_notes": 5, "valid_count": 3, "warning_count": 1, "error_count": 1}
    mock_client.orphans.return_value = [
        {"title": "Orphan", "external_id": "o-1"},
        {"title": "Orphan2", "external_id": "o-2"},
    ]
    mock_client.schema_diff.return_value = {
        "note_type": "task",
        "schema_found": True,
        "new_fields": [{"name": "extra_field", "count": 3, "total": 5, "percentage": 0.6}],
        "dropped_fields": [],
    }

    with patch("rich.prompt.Prompt.ask", side_effect=["", "task"]):
        with patch("bmh.workflows.lint.render_lint_all_dashboard") as mock_dash:
            mock_dash.return_value = MagicMock()
            flow_lint_all(mock_client)
            results_passed = mock_dash.call_args[0][0]
            assert results_passed["doctor_passed"] is False
            assert len(results_passed["orphans"]) == 2


def test_run_lint_hub_exits():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", return_value="0"):
        run_lint_hub(mock_client)  # Should exit cleanly
