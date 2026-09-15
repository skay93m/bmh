from __future__ import annotations

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch
import bmh.updater.engine as engine_mod
from bmh.updater.engine import _detect_environment, run_self_update


def test_detect_environment_git(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    dummy_file = tmp_path / "src" / "bmh" / "updater" / "engine.py"
    dummy_file.parent.mkdir(parents=True)
    dummy_file.touch()

    with patch.object(engine_mod, "__file__", str(dummy_file)):
        env_type, repo_path = _detect_environment()
        assert env_type == "git"
        assert repo_path == tmp_path


def test_detect_environment_uv_tool(tmp_path):
    dummy_file = tmp_path / "engine.py"
    dummy_file.touch()
    with patch.object(engine_mod, "__file__", str(dummy_file)):
        with patch("sys.executable", "/Users/user/.local/share/uv/tools/bmh/bin/python"):
            env_type, _ = _detect_environment()
            assert env_type == "uv_tool"


def test_detect_environment_uv_in_path(tmp_path):
    dummy_file = tmp_path / "engine.py"
    dummy_file.touch()
    with patch.object(engine_mod, "__file__", str(dummy_file)):
        with patch("sys.executable", "/usr/bin/python3"):
            with patch("shutil.which", side_effect=lambda x: "/bin/uv" if x == "uv" else None):
                env_type, _ = _detect_environment()
                assert env_type == "uv_tool"


def test_detect_environment_pipx_in_path(tmp_path):
    dummy_file = tmp_path / "engine.py"
    dummy_file.touch()
    with patch.object(engine_mod, "__file__", str(dummy_file)):
        with patch("sys.executable", "/usr/bin/python3"):
            with patch("shutil.which", side_effect=lambda x: "/bin/pipx" if x == "pipx" else None):
                env_type, _ = _detect_environment()
                assert env_type == "pipx"


def test_detect_environment_pipx(tmp_path):
    dummy_file = tmp_path / "engine.py"
    dummy_file.touch()
    with patch.object(engine_mod, "__file__", str(dummy_file)):
        with patch("sys.executable", "/Users/user/.local/pipx/venvs/bmh/bin/python"):
            env_type, _ = _detect_environment()
            assert env_type == "pipx"


def test_run_self_update_git_success():
    mock_run = subprocess.CompletedProcess(args=[], returncode=0, stdout="Updated", stderr="")
    with patch("bmh.updater.engine._detect_environment", return_value=("git", Path("/tmp/bmh"))):
        with patch("subprocess.run", return_value=mock_run) as run_call:
            res = run_self_update()
            assert res is True
            run_call.assert_called_once_with(
                ["git", "-C", "/tmp/bmh", "pull", "--ff-only"],
                capture_output=True,
                text=True,
                check=False,
            )


def test_run_self_update_git_failure():
    mock_run = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="merge conflict")
    with patch("bmh.updater.engine._detect_environment", return_value=("git", Path("/tmp/bmh"))):
        with patch("subprocess.run", return_value=mock_run):
            res = run_self_update()
            assert res is False


def test_run_self_update_git_exception():
    with patch("bmh.updater.engine._detect_environment", return_value=("git", Path("/tmp/bmh"))):
        with patch("subprocess.run", side_effect=OSError("Git not installed")):
            res = run_self_update()
            assert res is False


def test_run_self_update_uv_tool_success():
    mock_run = subprocess.CompletedProcess(args=[], returncode=0, stdout="Installed", stderr="")
    with patch("bmh.updater.engine._detect_environment", return_value=("uv_tool", None)):
        with patch("shutil.which", return_value="/usr/local/bin/uv"):
            with patch("subprocess.run", return_value=mock_run) as run_call:
                res = run_self_update()
                assert res is True
                assert run_call.call_args[0][0][0] == "uv"
                assert "tool" in run_call.call_args[0][0]


def test_run_self_update_uv_tool_failure():
    mock_run = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="Build failed")
    with patch("bmh.updater.engine._detect_environment", return_value=("uv_tool", None)):
        with patch("shutil.which", return_value="/usr/local/bin/uv"):
            with patch("subprocess.run", return_value=mock_run):
                res = run_self_update()
                assert res is False


def test_run_self_update_uv_tool_exception():
    with patch("bmh.updater.engine._detect_environment", return_value=("uv_tool", None)):
        with patch("shutil.which", return_value="/usr/local/bin/uv"):
            with patch("subprocess.run", side_effect=RuntimeError("Subprocess failed")):
                res = run_self_update()
                assert res is False


def test_run_self_update_pipx_success():
    mock_run = subprocess.CompletedProcess(args=[], returncode=0, stdout="Upgraded", stderr="")
    with patch("bmh.updater.engine._detect_environment", return_value=("pipx", None)):
        with patch("shutil.which", return_value="/usr/local/bin/pipx"):
            with patch("subprocess.run", return_value=mock_run) as run_call:
                res = run_self_update()
                assert res is True
                assert run_call.call_args[0][0][0] == "pipx"


def test_run_self_update_pipx_failure():
    mock_run = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="Pipx error")
    with patch("bmh.updater.engine._detect_environment", return_value=("pipx", None)):
        with patch("shutil.which", return_value="/usr/local/bin/pipx"):
            with patch("subprocess.run", return_value=mock_run):
                res = run_self_update()
                assert res is False


def test_run_self_update_pipx_exception():
    with patch("bmh.updater.engine._detect_environment", return_value=("pipx", None)):
        with patch("shutil.which", return_value="/usr/local/bin/pipx"):
            with patch("subprocess.run", side_effect=RuntimeError("Pipx failed")):
                res = run_self_update()
                assert res is False


def test_run_self_update_unknown_environment():
    with patch("bmh.updater.engine._detect_environment", return_value=("unknown", None)):
        with patch("shutil.which", return_value=None):
            res = run_self_update()
            assert res is False
