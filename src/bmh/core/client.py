from __future__ import annotations

import os
import shutil
import subprocess
from typing import List, Optional

from bmh.core.models import NoteModel, normalize_notes_json


class BMError(Exception):
    """Base exception for Basic Memory client errors."""
    pass


class BMNotFoundError(BMError):
    """Raised when the 'bm' CLI executable cannot be found in PATH."""
    pass


class BMExecutionError(BMError):
    """Raised when 'bm' command execution fails."""

    def __init__(self, message: str, exit_code: int, stderr: str, stdout: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout


class BMClient:
    """Subprocess client wrapper for the Basic Memory (bm) CLI."""

    def __init__(self, binary_path: Optional[str] = None):
        self.binary_path = binary_path or os.environ.get("BM_PATH") or shutil.which("bm")

    def is_available(self) -> bool:
        """Check if the bm executable is available and executable."""
        if not self.binary_path:
            return False
        return shutil.which(self.binary_path) is not None

    def execute(self, args: List[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
        """Execute a bm CLI command with arguments."""
        if not self.is_available():
            raise BMNotFoundError(
                "Basic Memory CLI ('bm') not found. Ensure 'bm' is installed and available in your PATH."
            )

        cmd = [self.binary_path, *args]  # type: ignore[list-item]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise BMError(f"Command timed out after {timeout} seconds: {' '.join(cmd)}") from e
        except Exception as e:
            raise BMError(f"Failed to execute bm command: {e}") from e

        if result.returncode != 0:
            raise BMExecutionError(
                f"bm command failed with exit code {result.returncode}",
                exit_code=result.returncode,
                stderr=result.stderr.strip(),
                stdout=result.stdout.strip(),
            )

        return result

    def search_notes(
        self,
        query: Optional[str] = None,
        project: Optional[str] = None,
        note_type: Optional[str] = None,
        status: Optional[str] = None,
        is_title: bool = False,
    ) -> List[NoteModel]:
        """Search notes in Basic Memory with structured filters."""
        args = ["tool", "search-notes"]

        if is_title:
            args.append("--title")

        if project:
            args.extend(["--project", project])

        if note_type:
            args.extend(["--type", note_type])

        if status:
            args.extend(["--status", status])

        args.append("--json")

        if query:
            args.append(query)

        result = self.execute(args)
        return normalize_notes_json(result.stdout)
