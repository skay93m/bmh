from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from bmh.core.models import NoteModel
from bmh.core.client import BMClient, BMError
from bmh.workflows.query import (
    flow_keyword_search,
    flow_active_tasks,
    flow_project_browser,
    flow_recent_notes,
    flow_note_reader,
    flow_guided_query_copilot,
    run_query_hub,
)


def test_flow_keyword_search_success():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = [NoteModel(title="Found Note", content="body")]

    with patch("rich.prompt.Prompt.ask", side_effect=["architecture", ""]):
        with patch("rich.prompt.Confirm.ask", return_value=False):
            with patch("bmh.workflows.query.render_note_cards") as mock_render:
                flow_keyword_search(mock_client)
                mock_render.assert_called_once()


def test_flow_keyword_search_empty_query():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", return_value=""):
        flow_keyword_search(mock_client)
    mock_client.search_notes.assert_not_called()


def test_flow_keyword_search_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.side_effect = BMError("Search failed")
    with patch("rich.prompt.Prompt.ask", side_effect=["query", ""]):
        with patch("rich.prompt.Confirm.ask", return_value=False):
            flow_keyword_search(mock_client)  # Should not raise


def test_flow_active_tasks_no_results():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = []

    with patch("rich.prompt.Prompt.ask", return_value=""):
        flow_active_tasks(mock_client)

    mock_client.search_notes.assert_called_once_with(
        query=None, project=None, note_type="task", status="active"
    )


def test_flow_active_tasks_with_step_checkoff():
    note_content = "# My Task\n\n## Steps\n- [ ] Step 1\n- [x] Step 2"
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = [
        NoteModel(title="My Task", content=note_content, permalink="kancil/tasks/my-task")
    ]
    mock_client.edit_note.return_value = {"status": "ok"}

    with patch("rich.prompt.Prompt.ask", side_effect=["", "1", "1"]):
        with patch("rich.prompt.Confirm.ask", side_effect=[True, True]):
            with patch("bmh.workflows.query.render_note_cards"):
                flow_active_tasks(mock_client)

    mock_client.edit_note.assert_called_once()
    call_kwargs = mock_client.edit_note.call_args[1]
    assert call_kwargs["operation"] == "find_replace"
    assert "[x]" in call_kwargs["content"]


def test_flow_active_tasks_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.side_effect = BMError("Task fetch failed")
    with patch("rich.prompt.Prompt.ask", return_value=""):
        flow_active_tasks(mock_client)  # Should not raise


def test_flow_project_browser():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = []

    with patch("rich.prompt.Prompt.ask", side_effect=["2", ""]):
        with patch("bmh.workflows.query.render_note_cards"):
            flow_project_browser(mock_client)

    mock_client.search_notes.assert_called_once_with(query=None, project="kensho")


def test_flow_recent_notes():
    mock_client = MagicMock(spec=BMClient)
    mock_client.recent_activity.return_value = [
        {"title": "Recent Note", "content": "body", "entity": "kancil/notes/recent"}
    ]

    with patch("rich.prompt.Prompt.ask", side_effect=["", "10"]):
        with patch("bmh.workflows.query.render_note_cards"):
            flow_recent_notes(mock_client)

    mock_client.recent_activity.assert_called_once()


def test_flow_recent_notes_empty():
    mock_client = MagicMock(spec=BMClient)
    mock_client.recent_activity.return_value = []

    with patch("rich.prompt.Prompt.ask", side_effect=["", "10"]):
        flow_recent_notes(mock_client)


def test_flow_note_reader_found():
    mock_client = MagicMock(spec=BMClient)
    mock_client.read_note.return_value = {
        "title": "Read Note",
        "content": "Some content",
        "entity": "kancil/notes/read",
    }

    with patch("rich.prompt.Prompt.ask", side_effect=["kancil/notes/read", ""]):
        with patch("bmh.workflows.query.render_note_card") as mock_card:
            mock_card.return_value = MagicMock()
            flow_note_reader(mock_client)

    mock_client.read_note.assert_called_once_with(identifier="kancil/notes/read", project=None)


def test_flow_note_reader_not_found():
    mock_client = MagicMock(spec=BMClient)
    mock_client.read_note.return_value = None
    with patch("rich.prompt.Prompt.ask", side_effect=["nonexistent", ""]):
        flow_note_reader(mock_client)  # Should not raise


def test_flow_note_reader_empty_identifier():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", return_value=""):
        flow_note_reader(mock_client)
    mock_client.read_note.assert_not_called()


def test_flow_guided_query_copilot_executes():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = [NoteModel(title="Guided Result", content="body")]

    with patch("rich.prompt.Prompt.ask", side_effect=[
        "my architecture notes",  # intent
        "1",  # type: any
        "2",  # project: kancil
        "1",  # date: any
    ]):
        with patch("rich.prompt.Confirm.ask", side_effect=[False, True]):  # no title_only, yes execute
            with patch("bmh.workflows.query.render_note_cards") as mock_render:
                flow_guided_query_copilot(mock_client)
                mock_render.assert_called_once()

    mock_client.search_notes.assert_called_once()
    kwargs = mock_client.search_notes.call_args[1]
    assert kwargs["query"] == "my architecture notes"
    assert kwargs["project"] == "kancil"


def test_flow_guided_query_copilot_task_with_status():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = []

    with patch("rich.prompt.Prompt.ask", side_effect=[
        "active work items",  # intent
        "2",  # type: task
        "1",  # project: all
        "1",  # date: any
        "2",  # status: active only
    ]):
        with patch("rich.prompt.Confirm.ask", side_effect=[False, True]):
            with patch("bmh.workflows.query.render_note_cards"):
                flow_guided_query_copilot(mock_client)

    kwargs = mock_client.search_notes.call_args[1]
    assert kwargs["note_type"] == "task"
    assert kwargs["status"] == "active"


def test_flow_guided_query_copilot_empty_intent():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", return_value=""):
        flow_guided_query_copilot(mock_client)
    mock_client.search_notes.assert_not_called()


def test_flow_guided_query_copilot_cancelled():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", side_effect=["something", "1", "1", "1"]):
        with patch("rich.prompt.Confirm.ask", side_effect=[False, False]):  # no title_only, no execute
            flow_guided_query_copilot(mock_client)
    mock_client.search_notes.assert_not_called()


def test_run_query_hub_exits():
    mock_client = MagicMock(spec=BMClient)
    with patch("rich.prompt.Prompt.ask", return_value="0"):
        run_query_hub(mock_client)  # Should exit cleanly
