from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch
import pytest

from bmh.core.client import BMClient, BMError, BMExecutionError, BMNotFoundError


def test_bm_client_availability(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/local/bin/bm" if cmd == "bm" else None)
    client = BMClient(binary_path="bm")
    assert client.is_available() is True

    monkeypatch.setattr("shutil.which", lambda cmd: None)
    client_missing = BMClient(binary_path=None)
    assert client_missing.is_available() is False


def test_bm_client_execute_missing_binary(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    client = BMClient(binary_path=None)
    with pytest.raises(BMNotFoundError, match="Basic Memory CLI .* not found"):
        client.execute(["tool", "search-notes"])


def test_bm_client_execute_success():
    client = BMClient(binary_path="/dummy/bm")
    client.is_available = MagicMock(return_value=True)

    mock_completed = subprocess.CompletedProcess(
        args=["/dummy/bm", "tool", "search-notes", "--json"],
        returncode=0,
        stdout='[{"title": "Note Test", "content": "Body Test"}]',
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_completed) as mock_run:
        res = client.execute(["tool", "search-notes", "--json"])
        assert res.returncode == 0
        mock_run.assert_called_once()


def test_bm_client_execute_non_zero():
    client = BMClient(binary_path="/dummy/bm")
    client.is_available = MagicMock(return_value=True)

    mock_failed = subprocess.CompletedProcess(
        args=["/dummy/bm", "tool", "search-notes"],
        returncode=1,
        stdout="",
        stderr="No search criteria specified",
    )

    with patch("subprocess.run", return_value=mock_failed):
        with pytest.raises(BMExecutionError) as exc_info:
            client.execute(["tool", "search-notes"])
        assert exc_info.value.exit_code == 1
        assert "No search criteria" in exc_info.value.stderr


def test_bm_client_execute_timeout():
    client = BMClient(binary_path="/dummy/bm")
    client.is_available = MagicMock(return_value=True)

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["bm"], timeout=5)):
        with pytest.raises(BMError, match="Command timed out"):
            client.execute(["tool", "search-notes"], timeout=5)


def test_bm_client_execute_generic_exception():
    client = BMClient(binary_path="/dummy/bm")
    client.is_available = MagicMock(return_value=True)

    with patch("subprocess.run", side_effect=OSError("Permission denied")):
        with pytest.raises(BMError, match="Failed to execute bm command"):
            client.execute(["tool", "search-notes"])


def test_bm_client_search_notes_args():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='[{"title": "Found Note", "content": "Found Content"}]',
            stderr="",
        )
    )

    notes = client.search_notes(
        query="architecture",
        project="kensho",
        note_type="spec",
        status="active",
        is_title=True,
    )

    assert len(notes) == 1
    assert notes[0].title == "Found Note"

    expected_args = [
        "tool",
        "search-notes",
        "--title",
        "--project",
        "kensho",
        "--type",
        "spec",
        "--status",
        "active",
        "--json",
        "architecture",
    ]
    client.execute.assert_called_once_with(expected_args)


def test_bm_client_init_bm_path():
    client = BMClient(bm_path="/custom/path/bm")
    assert client.binary_path == "/custom/path/bm"


def test_bm_client_execute_stdin_streaming():
    client = BMClient(binary_path="/dummy/bm")
    client.is_available = MagicMock(return_value=True)

    mock_completed = subprocess.CompletedProcess(
        args=["/dummy/bm", "tool", "write-note"],
        returncode=0,
        stdout='{"action": "created", "title": "Piped Note"}',
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_completed) as mock_run:
        res = client.execute(["tool", "write-note"], input="streamed markdown content")
        assert res.returncode == 0
        mock_run.assert_called_once_with(
            ["/dummy/bm", "tool", "write-note"],
            input="streamed markdown content",
            capture_output=True,
            text=True,
            timeout=30.0,
            check=False,
        )


def test_bm_client_search_notes_extra_options():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Raw output text",
            stderr="",
        )
    )

    # Test non-json output and multiple options
    notes = client.search_notes(
        query="test query",
        tags=["auth", "backend"],
        after_date="7d",
        page=2,
        page_size=25,
        json_output=False,
    )

    assert len(notes) == 1
    assert notes[0].title == "test query"
    assert notes[0].content == "Raw output text"

    expected_args = [
        "tool",
        "search-notes",
        "--tag",
        "auth",
        "--tag",
        "backend",
        "--after-date",
        "7d",
        "--page",
        "2",
        "--page-size",
        "25",
        "test query",
    ]
    client.execute.assert_called_once_with(expected_args)


def test_bm_client_write_note_success():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"title": "New Task", "permalink": "kancil/tasks/new-task", "action": "created"}',
            stderr="",
        )
    )

    res = client.write_note(
        title="New Task",
        folder="tasks",
        content="Task description",
        tags=["dev", "p0"],
        note_type="task",
        project="kancil",
        overwrite=True,
    )

    assert res["title"] == "New Task"
    assert res["action"] == "created"

    expected_args = [
        "tool",
        "write-note",
        "--title",
        "New Task",
        "--folder",
        "tasks",
        "--content",
        "Task description",
        "--tags",
        "dev,p0",
        "--type",
        "task",
        "--project",
        "kancil",
        "--overwrite",
    ]
    client.execute.assert_called_once_with(expected_args, input=None)


def test_bm_client_write_note_with_input_content():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"title": "Piped Note", "action": "created"}',
            stderr="",
        )
    )

    res = client.write_note(
        title="Piped Note",
        folder="inbox",
        input_content="# Piped Markdown Body",
    )

    assert res["action"] == "created"
    expected_args = ["tool", "write-note", "--title", "Piped Note", "--folder", "inbox"]
    client.execute.assert_called_once_with(expected_args, input="# Piped Markdown Body")


def test_bm_client_write_note_conflict_error_payload():
    client = BMClient(binary_path="/dummy/bm")
    err = BMExecutionError(
        message="Command failed",
        exit_code=1,
        stderr="Error: NOTE_ALREADY_EXISTS",
        stdout='{"title": "Existing", "action": "conflict", "error": "NOTE_ALREADY_EXISTS"}',
    )
    client.execute = MagicMock(side_effect=err)

    res = client.write_note(title="Existing", folder="notes", content="Body")
    assert res["action"] == "conflict"
    assert res["error"] == "NOTE_ALREADY_EXISTS"


def test_bm_client_edit_note_success():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"title": "Task 1", "operation": "append", "fileCreated": false}',
            stderr="",
        )
    )

    res = client.edit_note(
        identifier="tasks/task-1.md",
        operation="append",
        content="\n- [decision] Verified",
        find_text=None,
        section="## Observations",
        expected_replacements=1,
        project="kancil",
    )

    assert res["operation"] == "append"
    expected_args = [
        "tool",
        "edit-note",
        "tasks/task-1.md",
        "--operation",
        "append",
        "--content",
        "\n- [decision] Verified",
        "--section",
        "## Observations",
        "--project",
        "kancil",
    ]
    client.execute.assert_called_once_with(expected_args)


def test_bm_client_edit_note_error_payload():
    client = BMClient(binary_path="/dummy/bm")
    err = BMExecutionError(
        message="Command failed",
        exit_code=1,
        stderr="Target note not found",
        stdout='{"error": "Note does not exist"}',
    )
    client.execute = MagicMock(side_effect=err)

    res = client.edit_note(
        identifier="nonexistent.md",
        operation="append",
        content="data",
    )
    assert res["error"] == "Note does not exist"


def test_bm_client_read_note_success():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"title": "My Note", "content": "Note content", "permalink": "kancil/my-note"}',
            stderr="",
        )
    )

    note_data = client.read_note("kancil/my-note", project="kancil")
    assert note_data is not None
    assert note_data["title"] == "My Note"
    assert note_data["content"] == "Note content"


def test_bm_client_read_note_exit_zero_nulls_returns_none():
    client = BMClient(binary_path="/dummy/bm")
    # bm returns exit 0 with all nulls when note does not exist
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"title": null, "permalink": null, "file_path": null, "content": null, "frontmatter": null}',
            stderr="",
        )
    )

    note_data = client.read_note("nonexistent")
    assert note_data is None


def test_bm_client_read_note_execution_error_returns_none():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(side_effect=BMExecutionError("Failed", 1, "Not found", ""))

    note_data = client.read_note("nonexistent")
    assert note_data is None


def test_bm_client_schema_validate_success():
    client = BMClient(binary_path="/dummy/bm")
    payload = (
        '{"total_notes": 5, "valid_count": 5, "warning_count": 0, "error_count": 0, "results": []}'
    )
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr="")
    )

    res = client.schema_validate(target="Task", project="kancil")
    assert res["valid_count"] == 5
    client.execute.assert_called_once_with(["tool", "schema-validate", "Task", "--project", "kancil"])


def test_bm_client_schema_validate_exit_zero_error():
    client = BMClient(binary_path="/dummy/bm")
    payload = '{"error": "No notes found of type \'nonexistent\'"}'
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr="")
    )

    res = client.schema_validate(target="nonexistent")
    assert "error" in res
    assert "No notes found" in res["error"]


def test_bm_client_schema_validate_execution_error():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(side_effect=BMExecutionError("Failed", 1, "Validation failed", ""))

    res = client.schema_validate()
    assert "error" in res
    assert res["error_count"] == 1


def test_bm_client_schema_diff_success():
    client = BMClient(binary_path="/dummy/bm")
    payload = '{"note_type": "Task", "schema_found": true, "new_fields": [], "dropped_fields": []}'
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr="")
    )

    res = client.schema_diff(note_type="Task", project="kensho")
    assert res["schema_found"] is True
    client.execute.assert_called_once_with(["tool", "schema-diff", "Task", "--project", "kensho"])


def test_bm_client_schema_diff_exit_zero_error():
    client = BMClient(binary_path="/dummy/bm")
    payload = '{"error": "No schema found for type \'Unknown\'"}'
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr="")
    )

    res = client.schema_diff(note_type="Unknown")
    assert "error" in res
    assert "No schema found" in res["error"]


def test_bm_client_doctor_passed():
    client = BMClient(binary_path="/dummy/bm")
    doctor_output = """Running Basic Memory doctor checks...
OK Created doctor project: doctor-123
OK API write created file
OK Manual file written
Doctor checks passed.
"""
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=["doctor"], returncode=0, stdout=doctor_output, stderr="")
    )

    res = client.doctor()
    assert res["status"] == "passed"
    assert res["passed"] is True
    assert len(res["steps"]) == 3
    assert "Created doctor project: doctor-123" in res["steps"]
    assert "API write created file" in res["steps"]


def test_bm_client_doctor_failed():
    client = BMClient(binary_path="/dummy/bm")
    err = BMExecutionError(
        message="Doctor failed",
        exit_code=1,
        stderr="Doctor failed: storage mismatch",
        stdout="Running Basic Memory doctor checks...\nDoctor failed: storage mismatch",
    )
    client.execute = MagicMock(side_effect=err)

    res = client.doctor()
    assert res["status"] == "failed"
    assert res["passed"] is False
    assert "Doctor failed" in res["output"]


def test_bm_client_orphans_success():
    client = BMClient(binary_path="/dummy/bm")
    payload = '[{"title": "Unlinked", "note_type": "note", "file_path": "notes/u.md", "external_id": "u-1"}]'
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr="")
    )

    res = client.orphans(project="kancil")
    assert len(res) == 1
    assert res[0]["title"] == "Unlinked"
    client.execute.assert_called_once_with(["orphans", "--json", "--project", "kancil"])


def test_bm_client_orphans_empty():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="[]", stderr="")
    )

    res = client.orphans()
    assert res == []


def test_bm_client_recent_activity_success():
    client = BMClient(binary_path="/dummy/bm")
    payload = '[{"title": "Recent 1", "permalink": "kancil/recent-1", "created_at": "2026-09-15"}]'
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr="")
    )

    res = client.recent_activity(page=2, page_size=20, project="kancil")
    assert len(res) == 1
    assert res[0]["title"] == "Recent 1"
    client.execute.assert_called_once_with(
        ["tool", "recent-activity", "--json", "--project", "kancil", "--page", "2", "--page-size", "20"]
    )


def test_bm_client_list_projects_success():
    client = BMClient(binary_path="/dummy/bm")
    payload = '{"projects": [{"name": "kancil", "is_default": true}, {"name": "kensho", "is_default": false}]}'
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr="")
    )

    projects = client.list_projects()
    assert len(projects) == 2
    assert projects[0]["name"] == "kancil"
    assert projects[1]["name"] == "kensho"


def test_bm_client_write_note_string_tags_and_non_json_stdout():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="Created note successfully", stderr="")
    )

    res = client.write_note(
        title="Plain",
        folder="notes",
        tags="single-tag",
    )
    assert res["title"] == "Plain"
    assert res["action"] == "created"
    assert "Created note successfully" in res["output"]


def test_bm_client_write_note_reraises_on_non_json_error():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(side_effect=BMExecutionError("Failed", 1, "Unknown error", "Not JSON"))
    with pytest.raises(BMExecutionError):
        client.write_note(title="Plain", folder="notes")


def test_bm_client_edit_note_find_text_and_non_json_stdout():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="Edited cleanly", stderr="")
    )

    res = client.edit_note(
        identifier="notes/p.md",
        operation="find_replace",
        content="new text",
        find_text="old text",
        expected_replacements=2,
    )
    assert res["identifier"] == "notes/p.md"
    assert res["operation"] == "find_replace"


def test_bm_client_edit_note_reraises_on_non_json_error():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(side_effect=BMExecutionError("Failed", 1, "Crash", "Not JSON"))
    with pytest.raises(BMExecutionError):
        client.edit_note(identifier="foo", operation="append", content="bar")


def test_bm_client_schema_validate_json_error_payload():
    client = BMClient(binary_path="/dummy/bm")
    err = BMExecutionError("Failed", 1, "Schema error", '{"error": "Validation payload error", "total_notes": 0}')
    client.execute = MagicMock(side_effect=err)

    res = client.schema_validate()
    assert res["error"] == "Validation payload error"


def test_bm_client_schema_diff_json_error_payload():
    client = BMClient(binary_path="/dummy/bm")
    err = BMExecutionError("Failed", 1, "Diff error", '{"error": "Diff payload error", "schema_found": false}')
    client.execute = MagicMock(side_effect=err)

    res = client.schema_diff("Task")
    assert res["error"] == "Diff payload error"


def test_bm_client_doctor_unexpected_exception():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(side_effect=RuntimeError("System broken"))

    res = client.doctor()
    assert res["status"] == "failed"
    assert res["passed"] is False
    assert "System broken" in res["output"]


def test_bm_client_orphans_error_in_dict_and_execution_error():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='{"error": "DB locked"}', stderr="")
    )
    res = client.orphans()
    assert res == [{"error": "DB locked"}]

    # Test BMExecutionError with stdout JSON
    err = BMExecutionError("Failed", 1, "DB error", '[{"error": "Invalid project"}]')
    client.execute = MagicMock(side_effect=err)
    res_err = client.orphans()
    assert res_err == [{"error": "Invalid project"}]

    # Test BMExecutionError without JSON reraises
    err_raw = BMExecutionError("Failed", 1, "Fatal", "Fatal crash")
    client.execute = MagicMock(side_effect=err_raw)
    with pytest.raises(BMExecutionError):
        client.orphans()


def test_bm_client_recent_activity_dict_envelope():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"results": [{"title": "Wrapped Item"}]}',
            stderr="",
        )
    )
    items = client.recent_activity()
    assert len(items) == 1
    assert items[0]["title"] == "Wrapped Item"


def test_bm_client_list_projects_already_list_and_fallback():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='[{"name": "p1"}]', stderr="")
    )
    projects = client.list_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == "p1"

    # Fallback on invalid json
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="not json", stderr="")
    )
    assert client.list_projects() == []


def test_bm_client_read_note_non_dict_json():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='["not", "dict"]', stderr="")
    )
    assert client.read_note("some_note") is None


def test_bm_client_schema_validate_unexpected_exception():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(side_effect=RuntimeError("Unexpected error"))
    res = client.schema_validate()
    assert "Unexpected error" in res["error"]
    assert res["error_count"] == 1


def test_bm_client_schema_diff_unexpected_exception():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(side_effect=RuntimeError("Diff exploded"))
    res = client.schema_diff("Task")
    assert "Diff exploded" in res["error"]
    assert res["schema_found"] is False


def test_bm_client_orphans_empty_dict_fallback():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='{"other": "payload"}', stderr="")
    )
    assert client.orphans() == []


def test_bm_client_recent_activity_invalid_json():
    client = BMClient(binary_path="/dummy/bm")
    client.execute = MagicMock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="invalid json", stderr="")
    )
    assert client.recent_activity() == []



