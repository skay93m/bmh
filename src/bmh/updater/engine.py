from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console

console = Console()

REPO_URL = "https://github.com/skay93m/bmh.git"


def _detect_environment() -> Tuple[str, Optional[Path]]:
    """Detect whether bmh is running from a uv tool, pipx, or git-cloned install.

    Order of precedence (most specific first):
    1. uv tool install — sys.executable lives inside ~/.local/share/uv/tools/bmh/
    2. pipx — sys.executable lives inside ~/.local/share/pipx/venvs/bmh/
    3. git clone — any parent of __file__ contains a .git directory
    4. uv available on PATH — assume uv tool
    5. pipx available on PATH — assume pipx
    """
    executable = str(sys.executable) if sys.executable else ""

    # 1. uv tool install check
    if "uv/tools/bmh" in executable or ("uv" in executable and "tools" in executable and "bmh" in executable):
        return "uv_tool", None

    # 2. pipx check
    if "pipx/venvs/bmh" in executable or ("pipx" in executable and "bmh" in executable):
        return "pipx", None

    # 3. git clone check — walk __file__ parents looking for .git
    try:
        current_file = Path(__file__).resolve()
        for parent in [current_file] + list(current_file.parents):
            if (parent / ".git").is_dir():
                return "git", parent
    except Exception:
        pass

    # 4. Fallback: check installed CLI tools
    if shutil.which("uv"):
        return "uv_tool", None

    if shutil.which("pipx"):
        return "pipx", None

    return "unknown", None


def run_self_update() -> bool:
    """Execute the update flow appropriate for the current install environment."""
    console.print("\n[bold cyan]── 🔄 Updating bmh ──[/bold cyan]")

    env_type, repo_path = _detect_environment()

    if env_type == "git" and repo_path:
        console.print(f"[dim]Detected git repository at {repo_path}...[/dim]")
        try:
            with console.status("[cyan]Pulling latest changes from git origin...[/cyan]"):
                res = subprocess.run(
                    ["git", "-C", str(repo_path), "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            if res.returncode == 0:
                console.print("\n[bold green]✨ bmh successfully updated via git![/bold green]\n")
                return True
            else:
                console.print(f"\n[yellow]Could not update cleanly: {res.stderr.strip()}[/yellow]\n")
                return False
        except Exception as e:
            console.print(f"\n[bold red]Git update failed:[/bold red] {e}\n")
            return False

    elif env_type == "uv_tool" and shutil.which("uv"):
        console.print("[dim]Updating via 'uv tool' from GitHub...[/dim]")
        try:
            with console.status("[cyan]Running uv tool install --force...[/cyan]"):
                res = subprocess.run(
                    ["uv", "tool", "install", f"git+{REPO_URL}", "--force"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            if res.returncode == 0:
                console.print("\n[bold green]✨ bmh successfully upgraded via uv tool![/bold green]\n")
                return True
            else:
                err = res.stderr.strip()
                if "pyproject.toml" in err or "setup.py" in err:
                    console.print(
                        f"\n[yellow]Remote repo update returned an error (remote release may not have pyproject.toml yet):[/yellow]\n"
                        f"[dim]{err}[/dim]\n"
                    )
                else:
                    console.print(f"\n[yellow]uv tool update returned an error: {err}[/yellow]\n")
                return False
        except Exception as e:
            console.print(f"\n[bold red]uv update failed:[/bold red] {e}\n")
            return False

    elif env_type == "pipx" and shutil.which("pipx"):
        console.print("[dim]Updating via pipx...[/dim]")
        try:
            with console.status("[cyan]Running pipx upgrade...[/cyan]"):
                res = subprocess.run(
                    ["pipx", "upgrade", "bmh"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            if res.returncode == 0:
                console.print("\n[bold green]✨ bmh successfully upgraded via pipx![/bold green]\n")
                return True
            else:
                console.print(f"\n[yellow]pipx update returned an error: {res.stderr.strip()}[/yellow]\n")
                return False
        except Exception as e:
            console.print(f"\n[bold red]pipx update failed:[/bold red] {e}\n")
            return False

    else:
        console.print(
            "\n[yellow]Could not determine package manager automatically.[/yellow]\n"
            "To upgrade bmh to the latest release, run:\n"
            f"[bold cyan]uv tool install git+{REPO_URL} --force[/bold cyan]\n"
        )
        return False
