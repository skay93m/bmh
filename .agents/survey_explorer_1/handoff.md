# Handoff Report — Survey Explorer 1

## 1. Observation
- **Codebase Root**: `/Users/kancil/.bmh` on git branch `develop`.
- **Package Configuration** (`/Users/kancil/.bmh/pyproject.toml` lines 1-28):
  - Package: `bmh` version `2.0.0`, `requires-python = ">=3.12"`.
  - Dependencies: `pydantic>=2.7.0`, `rich>=13.7.0`, `typer>=0.12.0`.
  - Dev dependencies: `pytest>=8.0.0`, `pytest-cov>=5.0.0`.
  - Entry point: `bmh = "bmh.main:cli_entrypoint"`.
  - Build backend: `hatchling.build`.
- **Existing Directory Layout** (`find_by_name` on `src/` and `tests/`):
  - `src/bmh/` contains `main.py`, `core/` (`client.py`, `models.py`), `ui/` (`banner.py`, `cards.py`, `menu.py`), and `updater/` (`engine.py`).
  - `src/bmh/workflows/` does **not** exist.
  - `tests/` contains `test_banner.py`, `test_cards.py`, `test_client.py`, `test_main.py`, `test_menu.py`, `test_models.py`, `test_updater.py`.
- **Current Test Suite**:
  - Command: `uv run pytest --cov=bmh --cov-report=term-missing`
  - Result: `60 passed in 0.62s`, coverage: `98%` (411 total statements, 7 misses).
  - Command: `uv tool install . --force` succeeded completely.
- **Client Primitives** (`/Users/kancil/.bmh/src/bmh/core/client.py` lines 31-104):
  - Only `is_available()`, `execute(args, timeout)`, and `search_notes(query, project, note_type, status, is_title)` are implemented.
  - Missing commands: `write-note`, `edit-note`, `read-note`, `schema-validate`, `schema-diff`, `doctor`, `orphans`.
- **Host `bm` Executable**:
  - Found at `/Users/kancil/.local/bin/bm`.
  - Verified outputs for:
    - `bm tool schema-validate` returns JSON: `{"total_notes": 2, "valid_count": 2, "warning_count": 1, "error_count": 0, "results": [...]}`.
    - `bm tool schema-diff Task` returns JSON: `{"note_type": "Task", "schema_found": true, "new_fields": [...], "dropped_fields": [...]}`.
    - `bm orphans --json` returns JSON array: `[{"external_id": "...", "title": "...", "note_type": "...", "file_path": "..."}]`.
    - `bm doctor` returns text: `Doctor checks passed.`.
- **Interactive Gateway** (`/Users/kancil/.bmh/src/bmh/ui/menu.py` lines 120-154):
  - Implements flat 1-5, 0 menu: `1: Search notes`, `2: View active tasks`, `3: Browse by project`, `4: View recent notes`, `5: Update bmh`, `0: Exit`.
- **UI Observation Badges** (`/Users/kancil/.bmh/src/bmh/ui/cards.py` lines 27-32, 57-63):
  - `_highlight_observations` is defined for `[decision]`, `[insight]`, `[risk]`, `[todo]`, `[status]`, `[x]`, `[ ]`, but `render_note_card` passes `note.content` directly to `Markdown(content_body)` without calling `_highlight_observations`.

## 2. Logic Chain
1. **Observation**: `pyproject.toml` defines dependencies on `typer`, `rich`, and `pydantic`.
   - **Inference**: These dependencies are fully sufficient for all TUI prompts, table formatting, JSON parsing, and CLI entry points needed for R1-R5. No additional dependencies are required.
2. **Observation**: `src/bmh/workflows/` does not exist, and `src/bmh/ui/menu.py` contains the only interactive workflow flows.
   - **Inference**: To satisfy R1, R2, R3, and R4, a new package `src/bmh/workflows/` must be introduced with `ingest.py`, `query.py`, and `lint.py`. `menu.py` must be refactored into the gateway that routes to these three hubs.
3. **Observation**: `BMClient` only wraps `tool search-notes`.
   - **Inference**: To satisfy R5, R2, R3, and R4, `BMClient` must be expanded with typed wrappers for `write-note`, `edit-note`, `read-note`, `schema-validate`, `schema-diff`, `doctor`, and `orphans`.
4. **Observation**: `render_note_card` does not apply `_highlight_observations` to card contents.
   - **Inference**: To fulfill R5's card consistency requirement, `render_note_card` should be updated so observation badges and step indicators are rendered with Rich styling.
5. **Observation**: The current test suite has 60 tests passing with 98% coverage.
   - **Inference**: All refactoring must preserve existing test coverage while adding unit tests for new workflows (`test_ingest.py`, `test_query.py`, `test_lint.py`), ensuring 100% pass rates on `pytest`.

## 3. Caveats
- No caveats. All files in `src/bmh`, `tests/`, and host `bm` CLI command specifications have been directly inspected, executed, and verified.

## 4. Conclusion
The `bmh` codebase is healthy, modular, and ready for Tri-Modal expansion. Implementation should follow the phased plan:
- **M1**: Expand `src/bmh/core/client.py` (`BMClient`) with all 7 `bm` primitives, and enhance `src/bmh/ui/cards.py` with observation badges and diagnostic panels.
- **M2**: Implement `src/bmh/workflows/ingest.py` (Note Capture Wizard with 5 templates, Quick Observation Appender, and Piped Capture).
- **M3**: Implement `src/bmh/workflows/query.py` (Search/Task browsers, step checkoff, project explorer, note reader, and Guided Query Co-Pilot).
- **M4**: Implement `src/bmh/workflows/lint.py` (Schema validator, orphan inspector, sync doctor, schema drift analyzer, Lint All dashboard).
- **M5**: Restructure `src/bmh/ui/menu.py` into the Tri-Modal Hub navigation gateway, and wire stdin handling in `src/bmh/main.py`.

## 5. Verification Method
1. Verify report existence and completeness:
   ```bash
   test -f /Users/kancil/.bmh/.agents/survey_explorer_1/report.md
   ```
2. Verify existing test suite baseline:
   ```bash
   uv run pytest
   ```
3. Invalidation condition: If any existing test fails or if `BMClient` cannot be extended without breaking existing `test_client.py` contracts, the conclusion would need adjustment.
