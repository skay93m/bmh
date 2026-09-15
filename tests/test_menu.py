from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from bmh.core.client import BMClient, BMError, BMNotFoundError
from bmh.core.models import NoteModel
from bmh.ui.menu import (
    _handle_client_error,
    flow_active_tasks,
    flow_browse_project,
    flow_recent_notes,
    flow_search_notes,
    run_interactive_session,
)


def test_handle_client_error_not_found():
    with patch("bmh.ui.menu.console.print") as mock_print:
        _handle_client_error(BMNotFoundError("CLI not found"))
        mock_print.assert_called_once()
        assert "not found" in mock_print.call_args[0][0]


def test_handle_client_error_bm_error():
    with patch("bmh.ui.menu.console.print") as mock_print:
        _handle_client_error(BMError("Generic error"))
        mock_print.assert_called_once()
        assert "Basic Memory Error:" in mock_print.call_args[0][0]


def test_handle_client_error_unexpected():
    with patch("bmh.ui.menu.console.print") as mock_print:
        _handle_client_error(RuntimeError("Kaboom"))
        mock_print.assert_called_once()
        assert "Unexpected Error:" in mock_print.call_args[0][0]


def test_flow_search_notes():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = [
        NoteModel(title="Search Hit", content="Search Content")
    ]

    with patch("rich.prompt.Prompt.ask", side_effect=["test query", "kensho"]):
        with patch("rich.prompt.Confirm.ask", return_value=True):
            with patch("bmh.ui.menu.render_note_cards") as mock_render:
                flow_search_notes(mock_client)
                mock_client.search_notes.assert_called_once_with(
                    query="test query",
                    project="kensho",
                    is_title=True,
                )
                mock_render.assert_called_once()


def test_flow_search_notes_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.side_effect = BMError("Search failed")

    with patch("rich.prompt.Prompt.ask", side_effect=["", ""]):
        with patch("bmh.ui.menu._handle_client_error") as mock_err:
            flow_search_notes(mock_client)
            mock_err.assert_called_once()


def test_flow_active_tasks():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = [
        NoteModel(title="Active Task", content="Task Body")
    ]

    with patch("rich.prompt.Prompt.ask", return_value="kancil"):
        with patch("bmh.ui.menu.render_note_cards") as mock_render:
            flow_active_tasks(mock_client)
            mock_client.search_notes.assert_called_once_with(
                query=None,
                project="kancil",
                note_type="task",
                status="active",
            )
            mock_render.assert_called_once()


def test_flow_active_tasks_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.side_effect = BMError("Task fetch failed")

    with patch("rich.prompt.Prompt.ask", return_value=""):
        with patch("bmh.ui.menu._handle_client_error") as mock_err:
            flow_active_tasks(mock_client)
            mock_err.assert_called_once()


def test_flow_browse_project():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = []

    with patch("rich.prompt.Prompt.ask", side_effect=["2", "systems"]):
        with patch("bmh.ui.menu.render_note_cards") as mock_render:
            flow_browse_project(mock_client)
            mock_client.search_notes.assert_called_once_with(
                query="systems",
                project="kensho",
            )
            mock_render.assert_called_once()


def test_flow_browse_project_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.side_effect = BMError("Browse failed")

    with patch("rich.prompt.Prompt.ask", side_effect=["1", ""]):
        with patch("bmh.ui.menu._handle_client_error") as mock_err:
            flow_browse_project(mock_client)
            mock_err.assert_called_once()


def test_flow_recent_notes():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.return_value = []

    with patch("rich.prompt.Prompt.ask", return_value=""):
        with patch("bmh.ui.menu.render_note_cards") as mock_render:
            flow_recent_notes(mock_client)
            mock_client.search_notes.assert_called_once_with(
                query=None,
                project=None,
            )
            mock_render.assert_called_once()


def test_flow_recent_notes_error():
    mock_client = MagicMock(spec=BMClient)
    mock_client.search_notes.side_effect = BMError("Recent failed")

    with patch("rich.prompt.Prompt.ask", return_value=""):
        with patch("bmh.ui.menu._handle_client_error") as mock_err:
            flow_recent_notes(mock_client)
            mock_err.assert_called_once()


def test_run_interactive_session_options():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("bmh.ui.menu.flow_search_notes") as mock_search, \
             patch("bmh.ui.menu.flow_active_tasks") as mock_tasks, \
             patch("bmh.ui.menu.flow_browse_project") as mock_browse, \
             patch("bmh.ui.menu.flow_recent_notes") as mock_recent, \
             patch("bmh.updater.engine.run_self_update") as mock_update:

            # Test 1 -> search, then continue
            with patch("rich.prompt.Prompt.ask", side_effect=["1", "", "2", "", "3", "", "4", "", "5", "", "0"]):
                run_interactive_session(mock_client)
                mock_search.assert_called_once()
                mock_tasks.assert_called_once()
                mock_browse.assert_called_once()
                mock_recent.assert_called_once()
                mock_update.assert_called_once()


def test_run_interactive_session_quit_at_prompt():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("rich.prompt.Prompt.ask", side_effect=["1", "q"]):
            with patch("bmh.ui.menu.flow_search_notes"):
                run_interactive_session(mock_client)


def test_run_interactive_session_interrupt():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("rich.prompt.Prompt.ask", side_effect=KeyboardInterrupt):
            run_interactive_session(mock_client)
