from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

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

    def __init__(self, binary_path: Optional[str] = None, bm_path: Optional[str] = None):
        self.binary_path = binary_path or bm_path or os.environ.get("BM_PATH") or shutil.which("bm")

    def is_available(self) -> bool:
        """Check if the bm executable is available and executable."""
        if not self.binary_path:
            return False
        return shutil.which(self.binary_path) is not None

    def execute(
        self,
        args: List[str],
        timeout: float = 30.0,
        input: Optional[str] = None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a bm CLI command with arguments and optional stdin input."""
        if not self.is_available():
            raise BMNotFoundError(
                "Basic Memory CLI ('bm') not found. Ensure 'bm' is installed and available in your PATH."
            )

        cmd = [self.binary_path, *args]  # type: ignore[list-item]
        try:
            result = subprocess.run(
                cmd,
                input=input,
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
        json_output: bool = True,
        tags: Optional[List[str] | str] = None,
        after_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
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

        if tags:
            if isinstance(tags, str):
                args.extend(["--tag", tags])
            else:
                for t in tags:
                    args.extend(["--tag", str(t)])

        if after_date:
            args.extend(["--after-date", after_date])

        if page > 1:
            args.extend(["--page", str(page)])

        if page_size != 10:
            args.extend(["--page-size", str(page_size)])

        if json_output:
            args.append("--json")

        if query:
            args.append(query)

        result = self.execute(args)
        if json_output:
            return normalize_notes_json(result.stdout)
        return [NoteModel(title=query or "Search Output", content=result.stdout)]

    def write_note(
        self,
        title: str,
        folder: str,
        content: Optional[str] = None,
        tags: Optional[str | List[str]] = None,
        note_type: Optional[str] = None,
        project: Optional[str] = None,
        overwrite: bool = False,
        input_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Write a new note or overwrite existing note via bm tool write-note."""
        args = ["tool", "write-note", "--title", title, "--folder", folder]

        if content is not None:
            args.extend(["--content", content])

        if tags:
            if isinstance(tags, list):
                args.extend(["--tags", ",".join(tags)])
            else:
                args.extend(["--tags", str(tags)])

        if note_type:
            args.extend(["--type", note_type])

        if project:
            args.extend(["--project", project])

        if overwrite:
            args.append("--overwrite")

        stdin_data = input_content if input_content is not None else None

        try:
            result = self.execute(args, input=stdin_data)
            try:
                return json.loads(result.stdout)
            except Exception:
                return {
                    "title": title,
                    "folder": folder,
                    "action": "created",
                    "output": result.stdout,
                }
        except BMExecutionError as e:
            if e.stdout:
                try:
                    payload = json.loads(e.stdout)
                    if isinstance(payload, dict):
                        return payload
                except Exception:
                    pass
            raise

    def edit_note(
        self,
        identifier: str,
        operation: str,
        content: str,
        find_text: Optional[str] = None,
        section: Optional[str] = None,
        expected_replacements: int = 1,
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Edit an existing note via bm tool edit-note."""
        args = [
            "tool",
            "edit-note",
            identifier,
            "--operation",
            operation,
            "--content",
            content,
        ]

        if find_text is not None:
            args.extend(["--find-text", find_text])

        if section is not None:
            args.extend(["--section", section])

        if expected_replacements != 1:
            args.extend(["--expected-replacements", str(expected_replacements)])

        if project:
            args.extend(["--project", project])

        try:
            result = self.execute(args)
            try:
                return json.loads(result.stdout)
            except Exception:
                return {
                    "identifier": identifier,
                    "operation": operation,
                    "output": result.stdout,
                }
        except BMExecutionError as e:
            if e.stdout:
                try:
                    payload = json.loads(e.stdout)
                    if isinstance(payload, dict):
                        return payload
                except Exception:
                    pass
            raise

    def read_note(
        self,
        identifier: str,
        project: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Read an existing note by identifier via bm tool read-note --json.
        
        Handles exit 0 with null fields by returning None if note does not exist.
        """
        args = ["tool", "read-note", identifier, "--json"]
        if project:
            args.extend(["--project", project])

        try:
            result = self.execute(args)
        except BMExecutionError:
            return None

        try:
            data = json.loads(result.stdout)
        except Exception:
            return None

        if isinstance(data, dict):
            # If all identifying fields are None, note was not found
            if not data.get("title") and not data.get("content") and not data.get("permalink") and not data.get("file_path"):
                return None
            return data

        return None

    def schema_validate(
        self,
        target: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate schemas via bm tool schema-validate.
        
        Handles exit 0 with {'error': ...} when target type is not found.
        """
        args = ["tool", "schema-validate"]
        if target:
            args.append(target)
        if project:
            args.extend(["--project", project])

        try:
            result = self.execute(args)
            return json.loads(result.stdout)
        except BMExecutionError as e:
            if e.stdout:
                try:
                    return json.loads(e.stdout)
                except Exception:
                    pass
            return {"error": e.stderr or str(e), "total_notes": 0, "valid_count": 0, "warning_count": 0, "error_count": 1}
        except Exception as e:
            return {"error": str(e), "total_notes": 0, "valid_count": 0, "warning_count": 0, "error_count": 1}

    def schema_diff(
        self,
        note_type: str,
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze schema drift via bm tool schema-diff.
        
        Handles exit 0 with {'error': ...} when note type schema is not found.
        """
        args = ["tool", "schema-diff", note_type]
        if project:
            args.extend(["--project", project])

        try:
            result = self.execute(args)
            return json.loads(result.stdout)
        except BMExecutionError as e:
            if e.stdout:
                try:
                    return json.loads(e.stdout)
                except Exception:
                    pass
            return {"error": e.stderr or str(e), "note_type": note_type, "schema_found": False}
        except Exception as e:
            return {"error": str(e), "note_type": note_type, "schema_found": False}

    def doctor(self) -> Dict[str, Any]:
        """Execute bm doctor consistency check and parse output for status, steps, and passed flag."""
        args = ["doctor"]
        try:
            result = self.execute(args)
            output = result.stdout.strip()
            passed = "Doctor checks passed" in output or result.returncode == 0
        except BMExecutionError as e:
            output = (e.stdout + "\n" + e.stderr).strip()
            passed = False
        except Exception as e:
            return {
                "status": "failed",
                "passed": False,
                "output": str(e),
                "steps": [],
            }

        steps: List[str] = []
        for line in output.splitlines():
            line_str = line.strip()
            if line_str.startswith("OK "):
                steps.append(line_str[3:].strip())
            elif line_str.startswith("Running ") or line_str.startswith("Doctor "):
                continue
            elif line_str:
                steps.append(line_str)

        return {
            "status": "passed" if passed else "failed",
            "passed": passed,
            "output": output,
            "steps": steps,
        }

    def orphans(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve orphan entities (without relations) via bm orphans --json."""
        args = ["orphans", "--json"]
        if project:
            args.extend(["--project", project])

        try:
            result = self.execute(args)
            if not result.stdout or not result.stdout.strip():
                return []
            try:
                parsed = json.loads(result.stdout)
            except (json.JSONDecodeError, ValueError):
                return []
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "error" in parsed:
                return [{"error": parsed["error"]}]
            return []
        except BMExecutionError as e:
            if e.stdout:
                try:
                    parsed = json.loads(e.stdout)
                    if isinstance(parsed, list):
                        return parsed
                    if isinstance(parsed, dict) and "error" in parsed:
                        return [{"error": parsed["error"]}]
                except Exception:
                    pass
            raise

    def recent_activity(
        self,
        page: int = 1,
        page_size: int = 10,
        project: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent activity items via bm tool recent-activity --json."""
        args = ["tool", "recent-activity", "--json"]
        if project:
            args.extend(["--project", project])
        if page > 1:
            args.extend(["--page", str(page)])
        if page_size != 10:
            args.extend(["--page-size", str(page_size)])

        result = self.execute(args)
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for key in ("results", "items", "activity", "data"):
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
                return [parsed]
            return []
        except Exception:
            return []

    def list_projects(self) -> List[Dict[str, Any]]:
        """List registered Basic Memory projects via bm tool list-projects."""
        args = ["tool", "list-projects"]
        result = self.execute(args)
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict) and "projects" in parsed:
                return parsed["projects"]
            if isinstance(parsed, list):
                return parsed
            return []
        except Exception:
            return []

