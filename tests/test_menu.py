from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from bmh.core.client import BMClient, BMError, BMNotFoundError
from bmh.core.models import NoteModel
from bmh.ui.menu import (
    _handle_client_error,
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


def test_run_interactive_session_ingest():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("bmh.ui.menu.run_ingest_hub") as mock_ingest:
            with patch("rich.prompt.Prompt.ask", side_effect=["1", "0"]):
                run_interactive_session(mock_client)
                mock_ingest.assert_called_once_with(mock_client)


def test_run_interactive_session_query():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("bmh.ui.menu.run_query_hub") as mock_query:
            with patch("rich.prompt.Prompt.ask", side_effect=["2", "0"]):
                run_interactive_session(mock_client)
                mock_query.assert_called_once_with(mock_client)


def test_run_interactive_session_lint():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("bmh.ui.menu.run_lint_hub") as mock_lint:
            with patch("rich.prompt.Prompt.ask", side_effect=["3", "0"]):
                run_interactive_session(mock_client)
                mock_lint.assert_called_once_with(mock_client)


def test_run_interactive_session_update():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("bmh.ui.menu.run_self_update") as mock_update:
            with patch("rich.prompt.Prompt.ask", side_effect=["4", "0"]):
                run_interactive_session(mock_client)
                mock_update.assert_called_once()


def test_run_interactive_session_exit_zero():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("rich.prompt.Prompt.ask", return_value="0"):
            run_interactive_session(mock_client)  # Should exit cleanly


def test_run_interactive_session_exit_keyword():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("rich.prompt.Prompt.ask", return_value="quit"):
            run_interactive_session(mock_client)


def test_run_interactive_session_keyboard_interrupt():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("rich.prompt.Prompt.ask", side_effect=KeyboardInterrupt):
            run_interactive_session(mock_client)  # Should not raise


def test_run_interactive_session_eof():
    mock_client = MagicMock(spec=BMClient)
    with patch("bmh.ui.menu.render_banner"):
        with patch("rich.prompt.Prompt.ask", side_effect=EOFError):
            run_interactive_session(mock_client)  # Should not raise
