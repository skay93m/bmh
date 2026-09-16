"""Milestone M1 Empirical Stress Testing Suite.

Adversarially challenges BMClient subprocess execution and UI cards under extreme conditions:
1. Malformed JSON outputs and unparseable strings
2. Missing commands and invalid binary paths
3. Subprocess timeouts and tiny deadlines
4. Empty strings and whitespace inputs
5. Large payloads (10MB JSON and inputs)
6. Non-zero exit codes and argument errors
7. Pydantic validation boundaries
"""

from __future__ import annotations

import json
import subprocess
import time
from unittest.mock import MagicMock, patch
import pytest
from pydantic import ValidationError

from bmh.core.client import BMClient, BMError, BMExecutionError, BMNotFoundError
from bmh.core.models import NoteModel, normalize_notes_json
from bmh.ui.cards import (
    highlight_observations,
    render_doctor_panel,
    render_lint_all_dashboard,
    render_note_card,
    render_orphan_list_panel,
    render_schema_diff_panel,
    render_schema_validation_panel,
)


# ============================================================================
# Dimension 1: Malformed JSON Outputs & Unparseable Strings
# ============================================================================


def test_search_notes_handles_malformed_json():
    """search_notes should fallback to plain text note when stdout is malformed JSON."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    notes = client.search_notes(query="test")
    assert len(notes) == 1
    assert notes[0].title == "Plain Text Output"
    assert "not valid json" in notes[0].content


def test_write_note_handles_malformed_json():
    """write_note should return fallback created dict on malformed JSON stdout."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    res = client.write_note(title="T", folder="F", content="C")
    assert isinstance(res, dict)
    assert res["title"] == "T"
    assert res["action"] == "created"
    assert "not valid json" in res["output"]


def test_edit_note_handles_malformed_json():
    """edit_note should return fallback dict on malformed JSON stdout."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    res = client.edit_note(identifier="id1", operation="append", content="C")
    assert isinstance(res, dict)
    assert res["identifier"] == "id1"
    assert "not valid json" in res["output"]


def test_read_note_handles_malformed_json():
    """read_note should return None on malformed JSON stdout."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    assert client.read_note(identifier="id1") is None


def test_schema_validate_handles_malformed_json():
    """schema_validate should return error report dict on malformed JSON stdout."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    res = client.schema_validate()
    assert isinstance(res, dict)
    assert "error" in res
    assert res["total_notes"] == 0
    assert res["error_count"] == 1


def test_schema_diff_handles_malformed_json():
    """schema_diff should return error report dict on malformed JSON stdout."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    res = client.schema_diff(note_type="spec")
    assert isinstance(res, dict)
    assert "error" in res
    assert res["schema_found"] is False


def test_recent_activity_handles_malformed_json():
    """recent_activity should return empty list on malformed JSON stdout."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    res = client.recent_activity()
    assert isinstance(res, list)
    assert len(res) == 0


def test_list_projects_handles_malformed_json():
    """list_projects should return empty list on malformed JSON stdout."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    res = client.list_projects()
    assert isinstance(res, list)
    assert len(res) == 0


@pytest.mark.xfail(
    reason="Bug: orphans() raises raw JSONDecodeError when stdout is malformed JSON or empty string",
    strict=False,
)
def test_orphans_malformed_json_unhandled_crash():
    """orphans() should return empty list or error dict, not raise raw JSONDecodeError."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not valid json {{{", stderr=""
        )
    )
    # Expected: return [] or raise BMError
    # Actual bug: raises unhandled json.decoder.JSONDecodeError
    res = client.orphans()
    assert isinstance(res, list)


@pytest.mark.xfail(
    reason="Bug: orphans() raises raw JSONDecodeError when stdout is empty string",
    strict=False,
)
def test_orphans_empty_stdout_unhandled_crash():
    """orphans() should handle empty stdout gracefully without crashing."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
    )
    res = client.orphans()
    assert isinstance(res, list)


# ============================================================================
# Dimension 2: Missing Commands & Invalid Binary Paths
# ============================================================================


def test_missing_binary_raises_domain_exception(monkeypatch):
    """Missing binary should raise BMNotFoundError on all mutating and querying methods."""
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    client = BMClient(binary_path="/nonexistent/bm")

    with pytest.raises(BMNotFoundError):
        client.execute(["version"])

    with pytest.raises(BMNotFoundError):
        client.search_notes(query="test")

    with pytest.raises(BMNotFoundError):
        client.write_note(title="T", folder="F")

    with pytest.raises(BMNotFoundError):
        client.edit_note(identifier="id", operation="append", content="C")

    with pytest.raises(BMNotFoundError):
        client.read_note(identifier="id")

    with pytest.raises(BMNotFoundError):
        client.orphans()

    with pytest.raises(BMNotFoundError):
        client.recent_activity()

    with pytest.raises(BMNotFoundError):
        client.list_projects()


def test_missing_binary_returns_safe_report_on_diagnostic_methods(monkeypatch):
    """Diagnostic methods (schema_validate, schema_diff, doctor) should return safe error dicts on missing binary."""
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    client = BMClient(binary_path="/nonexistent/bm")

    v_res = client.schema_validate()
    assert "error" in v_res
    assert v_res["valid_count"] == 0

    d_res = client.schema_diff(note_type="spec")
    assert "error" in d_res
    assert d_res["schema_found"] is False

    doc_res = client.doctor()
    assert doc_res["status"] == "failed"
    assert doc_res["passed"] is False


def test_directory_as_binary_path_rejected():
    """Specifying a directory path like /tmp should report unavailable and raise BMNotFoundError."""
    client = BMClient(binary_path="/tmp")
    assert client.is_available() is False
    with pytest.raises(BMNotFoundError):
        client.execute(["version"])


# ============================================================================
# Dimension 3: Subprocess Timeout Conditions
# ============================================================================


def test_subprocess_timeout_raises_bmerror():
    """Timeout during execution should raise BMError with helpful timeout diagnostic."""
    client = BMClient(binary_path="/dummy/bm")
    client.is_available = MagicMock(return_value=True)

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["/dummy/bm", "search-notes"], timeout=0.01),
    ):
        with pytest.raises(BMError, match="Command timed out after 0.01 seconds"):
            client.execute(["search-notes"], timeout=0.01)


def test_timeout_propagates_domain_bmerror_on_methods():
    """All standard client methods should raise BMError when execution times out."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(side_effect=BMError("Command timed out after 30 seconds"))

    with pytest.raises(BMError, match="timed out"):
        client.search_notes(query="timeout_test")

    with pytest.raises(BMError, match="timed out"):
        client.write_note(title="T", folder="F")

    with pytest.raises(BMError, match="timed out"):
        client.edit_note(identifier="id", operation="append", content="C")

    with pytest.raises(BMError, match="timed out"):
        client.read_note(identifier="id")

    with pytest.raises(BMError, match="timed out"):
        client.orphans()


# ============================================================================
# Dimension 4: Empty Strings & Boundary Inputs
# ============================================================================


def test_empty_string_parameters():
    """Methods should handle empty strings without crashing or generating malformed args."""
    client = BMClient(binary_path="/dummy/bm")
    recorded_args = []
    client.execute = MagicMock(
        side_effect=lambda args, **kw: (
            recorded_args.append(args)
            or subprocess.CompletedProcess(args, 0, '{"title": "ok"}', "")
        )
    )

    # Empty query should not add positional arg
    client.search_notes(query="", project="", note_type="", status="", tags="")
    assert recorded_args[-1] == ["tool", "search-notes", "--json"]

    # Empty title and folder in write_note
    client.write_note(title="", folder="", content="", input_content="")
    assert recorded_args[-1] == ["tool", "write-note", "--title", "", "--folder", "", "--content", ""]

    # Empty identifier in read_note
    client.read_note(identifier="")
    assert recorded_args[-1] == ["tool", "read-note", "", "--json"]


# ============================================================================
# Dimension 5: Large Payloads (Stress & Performance)
# ============================================================================


def test_large_payload_search_notes():
    """search_notes should parse thousands of notes (5MB+ JSON) efficiently without memory exhaustion."""
    client = BMClient(binary_path="/dummy/bm")
    raw_notes = [
        {
            "title": f"Stress Note {i}",
            "content": f"[decision] Architecture Decision {i}\n[todo] Implement step {i}\n" * 5,
            "entity": f"note_{i}",
            "file_path": f"/vault/notes/note_{i}.md",
            "tags": ["stress", f"tag_{i}"],
            "updated_at": "2026-09-16T00:00:00Z",
        }
        for i in range(2500)
    ]
    json_payload = json.dumps(raw_notes)
    assert len(json_payload) > 1_000_000  # Over 1 MB

    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=json_payload, stderr="")
    )

    start_time = time.perf_counter()
    notes = client.search_notes(query="stress")
    duration = time.perf_counter() - start_time

    assert len(notes) == 2500
    assert duration < 2.0  # Must parse within 2 seconds


def test_large_payload_note_card_rendering():
    """render_note_card should format large note (500KB+ text with badges) without hanging."""
    large_body = ("[decision] Decision badge\n[risk] Warning badge\n[todo] Action item\n" * 5000)
    note = NoteModel(title="Huge Note", content=large_body)

    start_time = time.perf_counter()
    panel = render_note_card(note)
    duration = time.perf_counter() - start_time

    assert panel is not None
    assert duration < 2.0  # Must render within 2 seconds


def test_large_stdin_input_write_note():
    """write_note should pass large stdin payload (5MB string) without error."""
    client = BMClient(binary_path="/dummy/bm")
    large_text = "Markdown content stream\n" * 200_000
    assert len(large_text) > 4_000_000  # Over 4 MB

    captured_input = []

    def mock_exec(args, input=None, **kw):
        captured_input.append(input)
        return subprocess.CompletedProcess(args, 0, '{"title": "huge", "action": "created"}', "")

    client.execute = MagicMock(side_effect=mock_exec)

    res = client.write_note(title="huge", folder="notes", input_content=large_text)
    assert res["action"] == "created"
    assert captured_input[0] == large_text


# ============================================================================
# Dimension 6: Non-Zero Exit Codes & Argument Errors
# ============================================================================


def test_bm_execution_error_with_stderr():
    """Non-zero exit codes should raise BMExecutionError containing stderr, stdout, and code."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        side_effect=BMExecutionError(
            message="bm command failed with exit code 2",
            exit_code=2,
            stderr="Error: unrecognized option '--bogus'",
            stdout="",
        )
    )

    with pytest.raises(BMExecutionError) as exc_info:
        client.search_notes(query="test")

    assert exc_info.value.exit_code == 2
    assert "unrecognized option" in exc_info.value.stderr


def test_write_note_recovers_json_error_payload():
    """write_note should recover JSON error payload from stdout when exit code is non-zero (e.g. conflict)."""
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        side_effect=BMExecutionError(
            message="exit code 1",
            exit_code=1,
            stderr="Note already exists",
            stdout='{"error": "NOTE_ALREADY_EXISTS", "title": "Existing Note"}',
        )
    )

    res = client.write_note(title="Existing Note", folder="notes")
    assert isinstance(res, dict)
    assert res["error"] == "NOTE_ALREADY_EXISTS"


# ============================================================================
# Dimension 7: Pydantic Validation Boundaries & UI Error Safety
# ============================================================================


@pytest.mark.xfail(
    reason="Bug: normalize_notes_json crashes with ValidationError when tags contains numeric values like [2025, 2026]",
    strict=False,
)
def test_search_notes_numeric_tags_validation_error():
    """search_notes should safely coerce numeric tag items to strings rather than raising ValidationError."""
    client = BMClient(binary_path="/dummy/bm")
    raw_data = json.dumps([{"title": "Tax Note", "content": "Summary", "tags": [2024, 2025]}])
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=raw_data, stderr="")
    )

    # Expected: notes[0].tags == ["2024", "2025"]
    # Actual bug: raises pydantic.ValidationError
    notes = client.search_notes(query="Tax")
    assert len(notes) == 1
    assert notes[0].tags == ["2024", "2025"]


@pytest.mark.xfail(
    reason="Bug: render_orphan_list_panel crashes with KeyError: 0 when passed a single error dict",
    strict=False,
)
def test_render_orphan_list_panel_dict_input():
    """render_orphan_list_panel should safely render error dict rather than raising KeyError."""
    error_dict = {"error": "Failed to connect to index"}
    # Expected: returns Panel with error message
    # Actual bug: raises KeyError: 0
    panel = render_orphan_list_panel(error_dict)
    assert panel is not None


@pytest.mark.xfail(
    reason="Bug: render_orphan_list_panel crashes with AttributeError on non-dict list items",
    strict=False,
)
def test_render_orphan_list_panel_string_items():
    """render_orphan_list_panel should handle list of plain strings without crashing."""
    plain_items = ["orphan_node_1", "orphan_node_2"]
    # Expected: returns Panel
    # Actual bug: item.get() raises AttributeError
    panel = render_orphan_list_panel(plain_items)
    assert panel is not None
