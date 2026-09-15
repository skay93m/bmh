from __future__ import annotations

import io
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
import bmh.main as main_mod
from bmh.main import app, main

runner = CliRunner()


def test_main_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "bmh version" in result.output


def test_main_update_command():
    with patch("bmh.main.run_self_update", return_value=True) as mock_update:
        result = runner.invoke(app, ["update"])
        assert result.exit_code == 0
        mock_update.assert_called_once()


def test_main_update_command_failure():
    with patch("bmh.main.run_self_update", return_value=False):
        result = runner.invoke(app, ["update"])
        assert result.exit_code == 1


def test_main_piped_stdin():
    mock_json = '[{"title": "Piped Note", "content": "Piped Content"}]'
    with patch("bmh.main.render_note_cards") as mock_render:
        result = runner.invoke(app, [], input=mock_json)
        assert result.exit_code == 0
        mock_render.assert_called_once()


def test_main_piped_empty_stdin():
    result = runner.invoke(app, [], input="   ")
    assert result.exit_code == 0
    assert "No input provided on stdin" in result.output


def test_main_interactive_launch_direct():
    mock_ctx = MagicMock()
    mock_ctx.invoked_subcommand = None

    with patch("sys.stdin.isatty", return_value=True):
        with patch("bmh.main.run_interactive_session") as mock_session:
            main(mock_ctx)
            mock_session.assert_called_once()


def test_cli_entrypoint_keyboard_interrupt():
    with patch("bmh.main.app", side_effect=KeyboardInterrupt):
        with patch("bmh.main.sys.exit") as mock_exit:
            main_mod.cli_entrypoint()
            mock_exit.assert_called_once_with(0)
