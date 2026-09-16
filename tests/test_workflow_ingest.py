from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch
import pytest

from bmh.core.models import NoteModel
from bmh.core.client import BMClient, BMError
from bmh.workflows.ingest import (
    flow_capture_wizard,
    flow_observation_appender,
    TEMPLATES,
    _build_task_content,
    _build_insight_content,
    _build_meeting_content,
    _build_decision_content,
    _build_scratchpad_content,
)


# ── Template builder tests ────────────────────────────────────────────────────

def test_build_task_content_full():
    with patch("rich.prompt.Prompt.ask", side_effect=["alice", "high", "Step 1, Step 2", "Context here", "[[Related Note]]"]):
        content = _build_task_content("My Task", None)
    assert "My Task" in content
    assert "[assigned_to] alice" in content
    assert "[priority] high" in content
    assert "[status] active" in content
    assert "- [ ] Step 1" in content
    assert "- [ ] Step 2" in content
    assert "[[Related Note]]" in content


def test_build_task_content_minimal():
    with patch("rich.prompt.Prompt.ask", side_effect=["", "", "", "", ""]):
        content = _build_task_content("Empty Task", None)
    assert "Empty Task" in content
    assert "[status] active" in content


def test_build_insight_content():
    with patch("rich.prompt.Prompt.ask", side_effect=["Core concept", "Key learning point", "https://example.com"]):
        content = _build_insight_content("My Insight", None)
    assert "My Insight" in content
    assert "Core concept" in content
    assert "[insight] Key learning point" in content
    assert "https://example.com" in content


def test_build_meeting_content():
    with patch("rich.prompt.Prompt.ask", side_effect=["2026-09-16", "Alice, Bob", "Item 1, Item 2", "Go ahead", "Follow up"]):
        content = _build_meeting_content("Weekly Sync", None)
    assert "Weekly Sync" in content
    assert "2026-09-16" in content
    assert "Alice" in content
    assert "Item 1" in content
    assert "[decision] Go ahead" in content
    assert "- [ ] Follow up" in content


def test_build_decision_content():
    with patch("rich.prompt.Prompt.ask", side_effect=["Legacy system is slow", "Option A, Option B", "Option A", "Better performance", "Migration risk"]):
        content = _build_decision_content("Migrate DB", None)
    assert "Migrate DB" in content
    assert "Legacy system is slow" in content
    assert "[decision] Option A" in content
    assert "[risk] Migration risk" in content


def test_build_scratchpad_content():
    with patch("rich.prompt.Prompt.ask", return_value="Quick notes here\\nSecond line"):
        content = _build_scratchpad_content("My Scratch", None)
    assert "My Scratch" in content
    assert "Quick notes here" in content
    assert "Second line" in content


def test_templates_have_all_types():
    types = {t.note_type for t in TEMPLATES}
    assert "task" in types
    assert "insight" in types
    assert "meeting" in types
    assert "decision" in types
    assert "note" in types


# ── flow_capture_wizard tests ─────────────────────────────────────────────────

def test_flow_capture_wizard_creates_note():
    mock_client = MagicMock(spec=BMClient)
    mock_client.write_note.return_value = {"permalink": "notes/test-note"}

    with patch("rich.prompt.Prompt.ask", side_effect=[
        "1",           # template: Task
        "Test Note",   # title
        "",            # project
        "tasks",       # folder
        "task",        # tags
        "alice", "high", "Step 1", "Context", "",  # task builder
    ]):
        with patch("rich.prompt.Confirm.ask", return_value=True):
            flow_capture_wizard(mock_client)

    mock_client.write_note.assert_called_once()


def test_flow_capture_wizard_empty_title_returns():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", side_effect=["1", "", "", "tasks", "task", "a", "b", "c", "d", "e"]):
        with patch("rich.prompt.Confirm.ask", return_value=True):
            flow_capture_wizard(mock_client)
    mock_client.write_note.assert_not_called()


def test_flow_capture_wizard_cancelled():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", side_effect=[
        "1", "My Note", "", "tasks", "task",
        "alice", "medium", "", "desc", "",
    ]):
        with patch("rich.prompt.Confirm.ask", return_value=False):
            flow_capture_wizard(mock_client)
    mock_client.write_note.assert_not_called()


def test_flow_capture_wizard_write_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.write_note.side_effect = BMError("Write failed")
    with patch("rich.prompt.Prompt.ask", side_effect=[
        "1", "Task Note", "", "tasks", "task",
        "alice", "high", "", "", "",
    ]):
        with patch("rich.prompt.Confirm.ask", return_value=True):
            flow_capture_wizard(mock_client)  # Should not raise


# ── flow_observation_appender tests ──────────────────────────────────────────

def test_flow_observation_appender_success():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = [
        NoteModel(title="Target Note", entity="kancil/notes/target")
    ]
    mock_client.edit_note.return_value = {"status": "ok"}

    with patch("rich.prompt.Prompt.ask", side_effect=["search query", "", "1", "1", "Key decision"]):
        flow_observation_appender(mock_client)

    mock_client.edit_note.assert_called_once()
    call_kwargs = mock_client.edit_note.call_args[1]
    assert call_kwargs["operation"] == "append"
    assert "[decision]" in call_kwargs["content"]
    assert "Key decision" in call_kwargs["content"]


def test_flow_observation_appender_no_query():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", return_value=""):
        flow_observation_appender(mock_client)
    mock_client.search_notes.assert_not_called()


def test_flow_observation_appender_empty_results():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = []
    with patch("rich.prompt.Prompt.ask", side_effect=["missing note", ""]):
        flow_observation_appender(mock_client)
    mock_client.edit_note.assert_not_called()


def test_flow_observation_appender_empty_text():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = [NoteModel(title="Target Note", entity="kancil/notes/target")]
    with patch("rich.prompt.Prompt.ask", side_effect=["query", "", "1", "2", ""]):
        flow_observation_appender(mock_client)
    mock_client.edit_note.assert_not_called()


def test_flow_observation_appender_search_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.side_effect = BMError("Search failed")
    with patch("rich.prompt.Prompt.ask", side_effect=["query", ""]):
        flow_observation_appender(mock_client)  # Should not raise
