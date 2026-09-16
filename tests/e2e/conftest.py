from __future__ import annotations

import io
import subprocess
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
import pytest
from rich.console import Console
from typer.testing import CliRunner

from bmh.core.client import BMClient
from bmh.core.models import NoteModel


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide isolated Typer CliRunner."""
    return CliRunner()


@pytest.fixture
def capture_console() -> Console:
    """Rich Console that records output into string buffer."""
    return Console(record=True, file=io.StringIO(), force_terminal=False, color_system=None)


@pytest.fixture
def sample_note_model() -> NoteModel:
    """Sample NoteModel for testing."""
    return NoteModel(
        title="Daily Token Spend Optimisation",
        content="# Daily Token Spend Optimisation\n\nImplement automatic token measurement.\n\n## Steps\n1. [ ] Baseline measurement\n2. [x] Script automation\n\n## Observations\n- [status] active\n- [decision] Standardise on SQLite",
        entity="kancil/tasks/daily-token-spend-optimisation",
        external_id="8ff93f44-fdd2-4290-958c-75176432f8d1",
        file_path="tasks/daily-token-spend-optimisation.md",
        permalink="kancil/tasks/daily-token-spend-optimisation",
        updated_at="2026-09-15T05:10:58Z",
        note_type="task",
        metadata={"note_type": "task", "status": "active"},
    )


@pytest.fixture
def sample_search_json() -> str:
    """Sample search-notes JSON response."""
    return """{
      "results": [
        {
          "title": "Daily Token Spend Optimisation",
          "type": "entity",
          "score": 0.88,
          "entity": "kancil/tasks/daily-token-spend-optimisation",
          "external_id": "8ff93f44-fdd2-4290-958c-75176432f8d1",
          "permalink": "kancil/tasks/daily-token-spend-optimisation",
          "content": "# Daily Token Spend Optimisation\\n\\n## Steps\\n1. [ ] Step 1\\n2. [x] Step 2",
          "file_path": "tasks/daily-token-spend-optimisation.md",
          "updated_at": "2026-09-15T05:10:58Z",
          "metadata": {"note_type": "task"}
        }
      ],
      "current_page": 1,
      "page_size": 10,
      "total": 1,
      "total_is_exact": true,
      "has_more": false
    }"""


@pytest.fixture
def mock_bm_client(sample_note_model: NoteModel) -> MagicMock:
    """Comprehensive mock BMClient conforming to PROJECT.md interface contracts."""
    client = MagicMock(spec=BMClient)
    client.is_available.return_value = True

    # 1. search_notes
    client.search_notes.return_value = [sample_note_model]

    # 2. write_note
    client.write_note.return_value = {
        "title": "Sample Note",
        "permalink": "kancil/notes/sample-note",
        "file_path": "notes/sample-note.md",
        "checksum": "a1b2c3d4e5f6",
        "action": "created",
    }

    # 3. edit_note
    client.edit_note.return_value = {
        "title": "Sample Note",
        "permalink": "kancil/notes/sample-note",
        "file_path": "notes/sample-note.md",
        "checksum": "f8a9b2c1d4e3",
        "operation": "append",
        "fileCreated": False,
    }

    # 4. read_note
    client.read_note.return_value = {
        "title": "Daily Token Spend Optimisation",
        "permalink": "kancil/tasks/daily-token-spend-optimisation",
        "file_path": "tasks/daily-token-spend-optimisation.md",
        "content": "# Daily Token Spend Optimisation\n\nImplement automatic token measurement.\n\n## Steps\n1. [ ] Baseline measurement\n2. [x] Script automation\n\n## Observations\n- [status] active\n- [decision] Standardise on SQLite",
        "frontmatter": {
            "title": "Daily Token Spend Optimisation",
            "type": "task",
            "permalink": "kancil/tasks/daily-token-spend-optimisation",
            "status": "active",
            "priority": "high",
        },
    }

    # 5. schema_validate
    client.schema_validate.return_value = {
        "total_notes": 2,
        "total_entities": 2,
        "valid_count": 2,
        "warning_count": 0,
        "error_count": 0,
        "results": [
            {
                "note_identifier": "TASK-020",
                "schema_entity": "Task",
                "passed": True,
                "field_results": [
                    {
                        "field_name": "description",
                        "field_type": "string",
                        "required": True,
                        "status": "present",
                        "values": ["Implement token tracking"],
                        "message": "",
                    }
                ],
                "unmatched_observations": {},
                "unmatched_relations": [],
                "warnings": [],
                "errors": [],
            }
        ],
        "type_summaries": [
            {
                "note_type": "Task",
                "total_notes": 2,
                "total_entities": 2,
                "valid_count": 2,
                "warning_count": 0,
                "error_count": 0,
            }
        ],
    }

    # 6. schema_diff
    client.schema_diff.return_value = {
        "note_type": "Task",
        "schema_found": True,
        "new_fields": [],
        "dropped_fields": [],
        "cardinality_changes": [],
    }

    # 7. doctor
    client.doctor.return_value = {
        "status": "passed",
        "output": "Doctor checks passed.",
        "steps": [
            "Created doctor project: doctor-b8b4f0de",
            "API write created file",
            "Manual file written",
            "Project index processed manual file",
            "Search confirmed manual file",
            "Status observed indexed file",
        ],
    }

    # 8. orphans
    client.orphans.return_value = [
        {
            "external_id": "e07bad16-42ad-4725-83e0-c21fa9061e36",
            "title": "architecture",
            "note_type": "note",
            "file_path": "architecture/architecture.md",
        }
    ]

    # 9. recent_activity
    client.recent_activity.return_value = [
        {
            "type": "entity",
            "title": "Daily Token Spend Optimisation",
            "permalink": "kancil/tasks/daily-token-spend-optimisation",
            "file_path": "tasks/daily-token-spend-optimisation.md",
            "created_at": "2026-09-15T19:38:19Z",
        }
    ]

    # 10. list_projects
    client.list_projects.return_value = [
        {"name": "kancil", "is_default": True, "path": "/Users/kancil/kancil", "source": "local+cloud"},
        {"name": "kensho", "is_default": False, "path": "/Users/kancil/kensho", "source": "local+cloud"},
    ]

    return client


@pytest.fixture(autouse=True)
def guard_live_subprocess(monkeypatch):
    """Safety guard: prevent any unmocked subprocess call from running live bm commands."""
    real_run = subprocess.run

    def safe_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        # If command touches 'bm', verify it's under test interception
        if cmd and isinstance(cmd, list) and any("bm" in str(arg) for arg in cmd):
            # If executing real bm binary, raise to protect live notes
            if any(str(arg).endswith("/bm") or arg == "bm" for arg in cmd):
                raise RuntimeError(
                    f"Live 'bm' execution prevented by test safety guard: {cmd}. "
                    "Use mock_bm_client or mock subprocess.run in tests."
                )
        return real_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", safe_run)
