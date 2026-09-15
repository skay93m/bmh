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
