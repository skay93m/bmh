# Comprehensive Codebase Survey & Gap Analysis Report
**Component**: `bmh` (Basic Memory Helper)  
**Author**: Survey Explorer 1  
**Date**: 2026-09-15 / 2026-09-16  
**Status**: Completed  

---

## 1. Executive Summary

`bmh` (Basic Memory Helper) is currently at version `2.0.0`, implemented in modern Python 3.12+ using **Typer** (CLI interface), **Rich** (terminal formatting and TUI prompts), and **Pydantic v2** (data modeling and schema normalization). It has a clean, well-tested foundation with **60 unit tests** passing at **98% line coverage**.

However, the existing codebase only covers a subset of read-only query capabilities (`search`, `active-tasks`, `browse-project`, `recent-notes`) arranged in a single flat interactive menu, along with a self-updater and stdin JSON card renderer.

To fulfill the requirements of the **Tri-Modal Architecture (Ingest, Query, Lint)** defined in `ORIGINAL_REQUEST.md` (R1–R5):
1. The **Workflows layer** (`src/bmh/workflows/`) does not exist and must be created with `ingest.py`, `query.py`, and `lint.py`.
2. The **Interactive Navigation** (`src/bmh/ui/menu.py`) must be restructured from the current flat menu into three top-level hubs (`[1] Ingest`, `[2] Query`, `[3] Lint`), preserving `[4] Update` and `[0] Exit`.
3. The **Subprocess Client** (`src/bmh/core/client.py`) only implements `search_notes`; it must be expanded with 7 additional primitives (`write_note`, `edit_note`, `read_note`, `schema_validate`, `schema_diff`, `doctor`, `orphans`).
4. The **UI Components** (`src/bmh/ui/cards.py`) must integrate observation badge highlighting into markdown rendering and provide specialized Rich renderables for diagnostics and dashboards.
5. No new external Python dependencies are required; the current dependencies (`typer`, `rich`, `pydantic`) are fully adequate.

---

## 2. Project & Build Configuration

### 2.1 `pyproject.toml`
- **Build Backend**: `hatchling.build`
- **Requires-Python**: `>=3.12` (running Python 3.14.7 on macOS Darwin arm64)
- **Runtime Dependencies**:
  - `pydantic>=2.7.0` (installed: `2.13.5`)
  - `rich>=13.7.0` (installed: `15.0.0`)
  - `typer>=0.12.0` (installed: `0.27.2`)
- **Development Dependencies**:
  - `pytest>=8.0.0` (installed: `9.1.1`)
  - `pytest-cov>=5.0.0` (installed: `7.1.0`)
- **CLI Entrypoint**: `bmh = "bmh.main:cli_entrypoint"`
- **Verification**: `uv tool install . --force` and `uv run pytest` both succeed without errors.

### 2.2 Git & Project Metadata
- **Current Branch**: `develop` (clean working tree aside from `.agents/` metadata).
- **Commit Convention**: Commitizen conventional commits configured in `.cz.json` (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
- **Documentation**:
  - `AGENTS.md`: Outlines developer principles, branching rules, and card formatting invariants.
  - `ROADMAP.md`: Highlights Horizon 1 (shipped), Horizon 2 (Capture, Authoring & Task Progression - P0/P1), Horizon 3 (Context & Graph Traversal).
  - `BACKLOG.md`: Tracks STORY-001 through STORY-010.

---

## 3. Existing Codebase Architecture

```
/Users/kancil/.bmh/
├── pyproject.toml
├── Makefile
├── src/
│   └── bmh/
│       ├── __init__.py          # Exports __version__ = "2.0.0"
│       ├── main.py              # Typer app, --version, update cmd, stdin detection
│       ├── core/
│       │   ├── __init__.py      # Re-exports models and client
│       │   ├── client.py        # Subprocess wrapper for 'bm' (search_notes only)
│       │   └── models.py        # NoteModel, SearchResult, normalize_notes_json
│       ├── ui/
│       │   ├── __init__.py      # Re-exports banner, cards, menu
│       │   ├── banner.py        # Rich ASCII/gradient header banner
│       │   ├── cards.py         # Panel renderer with Markdown & metadata subtitle
│       │   └── menu.py          # Flat interactive menu (1-5, 0) & query flows
│       └── updater/
│           ├── __init__.py      # Re-exports run_self_update
│           └── engine.py        # Multi-environment updater (git, uv tool, pipx)
└── tests/
    ├── test_banner.py           # 1 test
    ├── test_cards.py            # 6 tests
    ├── test_client.py           # 7 tests
    ├── test_main.py             # 7 tests
    ├── test_menu.py             # 14 tests
    ├── test_models.py           # 10 tests
    └── test_updater.py          # 15 tests
```

### 3.1 Module-by-Module Assessment

#### `src/bmh/main.py`
- Typer application with `cli_entrypoint()`.
- Catches `KeyboardInterrupt` and `EOFError` gracefully.
- Stdin check via `not sys.stdin.isatty()`: parses input with `normalize_notes_json(input_data)` and renders cards.
- Interactive mode triggers `run_interactive_session()` from `bmh.ui.menu`.
- Subcommand `bmh update` calls `run_self_update()`.

#### `src/bmh/core/client.py`
- `BMClient`: Resolves binary path via `binary_path` arg, `BM_PATH` env var, or `shutil.which("bm")`.
- `execute(args, timeout=30.0)`: Wraps `subprocess.run(capture_output=True, text=True)`.
  - Raises `BMNotFoundError` if `bm` is missing.
  - Raises `BMExecutionError` if `returncode != 0` (includes exit code, stderr, stdout).
  - Raises `BMError` on timeout or general OS exceptions.
- `search_notes(...)`: Formats `["tool", "search-notes", ...]` with optional `--title`, `--project`, `--type`, `--status`, `--json`, and parses via `normalize_notes_json(result.stdout)`.
- **Gap**: Missing primitives for note writing, editing, reading, schema validation, schema diff, doctor, and orphans.

#### `src/bmh/core/models.py`
- `NoteModel`: Pydantic model with fields `title`, `content`, `entity`, `external_id`, `file_path`, `permalink`, `updated_at`, `note_type`, `metadata`.
- Normalization logic: `normalize_notes_json(data)` handles:
  - JSON strings (lists, dicts, wrapper keys `results`, `items`, `notes`, `data`, `rows`).
  - Fallback to single `NoteModel(title="Plain Text Output", content=data)` if JSON decoding fails.
- Robust, tested, and ready for reuse across all workflows.

#### `src/bmh/ui/cards.py`
- `render_note_card(note, index, total)`: Renders Rich `Panel` with `📌 Title [i/n]`, Markdown body, and footer `entity: ... | external_id: ... | file: ... | updated: ...`.
- Contains `_highlight_observations` with regex replacements for `[decision]`, `[insight]`, `[risk]`, `[todo]`, `[status]`, `[x]`, `[ ]`.
- **Gap**: `_highlight_observations` is currently not wired into `render_note_card` (it passes `note.content` directly to `Markdown(content_body)`). In addition, specialized cards for lint reports and interview steps are needed.

#### `src/bmh/ui/menu.py`
- Contains existing flows: `flow_search_notes`, `flow_active_tasks`, `flow_browse_project`, `flow_recent_notes`.
- Contains `_handle_client_error` helper for `BMNotFoundError`, `BMError`, and generic exceptions.
- `run_interactive_session()` presents options `1..5, 0`:
  `1: Search notes`, `2: View active tasks`, `3: Browse by project`, `4: View recent notes`, `5: Update bmh`, `0: Exit`.
- **Gap**: Needs restructuring into Tri-Modal Hub navigation.

#### `src/bmh/updater/engine.py`
- Handles updates across git repos, `uv tool`, and `pipx`. Fully tested (15 tests) and working.

---

## 4. Requirement-by-Requirement Gap Analysis

### R1. Tri-Modal Interactive Gateway & Navigation
| Aspect | Current State | Required State | Delta / Work Needed |
| :--- | :--- | :--- | :--- |
| Top-level Menu | Flat 6-item menu (1-5, 0) in `ui/menu.py` | 3 top-level operational hubs: `[1] Ingest`, `[2] Query`, `[3] Lint`, `[4] Update`, `[0] Exit` | Restructure `run_interactive_session()` in `menu.py` to dispatch to hub routers. |
| Submenus | None | Dedicated interactive sub-menu for each hub with back/exit options | Implement submenus in `ingest.py`, `query.py`, `lint.py`. |
| Piped Input | Stdin piped JSON handled in `main.py` | Piped JSON stream formatted into Rich cards; raw text handled for capture | Enhance stdin handling in `main.py` / `ingest.py`. |
| Error Handling | Handled in `menu.py` for search/task flows | Universal error handling for all hubs and missing `bm` binaries | Centralize error handling across all hub dispatches. |

### R2. Ingest Hub (`src/bmh/workflows/ingest.py`)
| Aspect | Current State | Required State | Delta / Work Needed |
| :--- | :--- | :--- | :--- |
| Module File | Does not exist | `src/bmh/workflows/ingest.py` | Create file and workflow functions. |
| Note Capture Wizard | None | Interactive wizard with 5 structured templates: Task, Insight, Meeting, Decision, Scratchpad | Build prompt wizard generating canonical frontmatter and observations, invoking `client.write_note(...)`. |
| Observation Appender | None | Search/select existing note and append tagged observations (`[decision]`, `[risk]`, `[insight]`, `[todo]`) | Build note selection prompt, tag picker, and invoke `client.edit_note(..., operation="append")`. |
| Piped Capture Handler | None | Ingest raw markdown/text from stdin into target notes | Build capture handler allowing target project/note specification for stdin data. |

### R3. Query Hub & Guided Query Co-Pilot (`src/bmh/workflows/query.py`)
| Aspect | Current State | Required State | Delta / Work Needed |
| :--- | :--- | :--- | :--- |
| Module File | Does not exist; basic flows in `menu.py` | `src/bmh/workflows/query.py` | Create file and migrate/expand query flows. |
| Search & Browsers | Basic search, tasks, project, recent in `menu.py` | Search, task browser, project explorer (`kancil`/`kensho`), recent activity timeline | Refactor into `query.py` with enhanced filters and rich card rendering. |
| Task Step Checkoff | Active tasks displayed as cards only | Interactive inspector allowing step selection and marking `[ ]` -> `[x]` | Parse checklist steps from task content, prompt user to check off step, call `client.edit_note(...)`. |
| Detail Note Reader | None | Interactive reader for selected notes | Implement note viewer displaying full content with Rich syntax highlighting. |
| Guided Query Co-Pilot | None | Interactive interview workflow (intent, scope, type, topics) formulating precise queries | Implement multi-step Co-Pilot interview, query builder, retrieval execution, and summary presentation. |

### R4. Lint Hub & Health Diagnostics (`src/bmh/workflows/lint.py`)
| Aspect | Current State | Required State | Delta / Work Needed |
| :--- | :--- | :--- | :--- |
| Module File | Does not exist | `src/bmh/workflows/lint.py` | Create file and diagnostic workflow functions. |
| Schema Validator | None | Validates frontmatter/schemas via `bm tool schema-validate` | Call `client.schema_validate(...)`, render formatted summary table of valid/warning/error counts and field issues. |
| Orphan Link Inspector | None | Detects unlinked entities via `bm orphans --json` | Call `client.orphans(...)`, render orphan count, entity list, and paths in Rich table/card. |
| Sync & Index Doctor | None | Checks index/db consistency via `bm doctor` | Call `client.doctor()`, render check status and OK/failure indicators. |
| Schema Drift Analyzer | None | Analyzes drift via `bm tool schema-diff` | Prompt for note type, call `client.schema_diff(...)`, render table of new/dropped fields and percentages. |
| 'Lint All' Dashboard | None | Unified diagnostic execution and health score | Run all 4 checks, calculate health score/grade, render unified Rich summary dashboard. |

### R5. Subprocess Execution & UI Consistency
| Aspect | Current State | Required State | Delta / Work Needed |
| :--- | :--- | :--- | :--- |
| Subprocess Primitives | `client.py` has `search_notes` only | Full primitives in `client.py` for: `write-note`, `edit-note`, `read-note`, `schema-validate`, `schema-diff`, `doctor`, `orphans` | Implement 7 new typed methods on `BMClient` with complete argument support and error handling. |
| Observation Badges | `_highlight_observations` in `cards.py` exists but is unused | Syntax-highlighted Markdown and observation badges integrated into cards | Update `render_note_card` to apply observation badge highlights or custom Rich renderables. |
| Diagnostic UI Cards | Only `NoteModel` cards exist | Specialized card/table renderers for Lint reports, Co-Pilot, and Task checkoffs | Add diagnostic Rich formatting helpers in `cards.py` or workflow modules. |

---

## 5. Subprocess Commands & Contracts Reference

Investigation of the host's `/Users/kancil/.local/bin/bm` binary confirmed exact command syntax and output shapes:

1. **`write-note`**:
   `bm tool write-note --title <title> --folder <folder> --content <content> [--tags <tags>] [--type <type>] [--project <project>] [--overwrite]`
2. **`edit-note`**:
   `bm tool edit-note <identifier> --operation <append|prepend|find_replace|replace_section> --content <content> [--find-text <text>] [--section <sec>] [--project <project>]`
3. **`read-note`**:
   `bm tool read-note <identifier> [--project <project>]`
4. **`schema-validate`**:
   `bm tool schema-validate [target] [--project <project>]` (outputs JSON object with `total_notes`, `valid_count`, `warning_count`, `error_count`, `results`, `type_summaries`)
5. **`schema-diff`**:
   `bm tool schema-diff <note_type> [--project <project>]` (outputs JSON object with `note_type`, `new_fields`, `dropped_fields`, `cardinality_changes`)
6. **`doctor`**:
   `bm doctor` (outputs plain text with checks like `OK Created doctor project...`, `Doctor checks passed.`)
7. **`orphans`**:
   `bm orphans --json [--project <project>]` (outputs JSON array of objects: `[{"external_id": "...", "title": "...", "note_type": "...", "file_path": "..."}, ...]`)

---

## 6. Testing Baseline & Impact Analysis

- **Current Suite**: 60 tests in `tests/`, 100% passing, 98% coverage.
- **Backward Compatibility**:
  - `tests/test_menu.py` tests `flow_search_notes`, `flow_active_tasks`, etc., and the 5-option interactive session.
  - When refactoring `menu.py` to the Tri-Modal layout, `test_menu.py` will need updates to reflect the new top-level choices (`1: Ingest`, `2: Query`, `3: Lint`, `4: Update`, `0: Exit`).
  - Existing query flows can be maintained as re-exports in `menu.py` or migrated to `query.py` with compatibility aliases.
- **New Test Requirements**:
  - `tests/test_client.py`: Add unit tests for `write_note`, `edit_note`, `read_note`, `schema_validate`, `schema_diff`, `doctor`, `orphans`.
  - `tests/test_ingest.py`: Add unit tests for 5 note templates, frontmatter generation, note capture wizard, observation appender, piped capture.
  - `tests/test_query.py`: Add unit tests for search browser, task step checkoff, project explorer, recent notes, detail note reader, Guided Query Co-Pilot interview.
  - `tests/test_lint.py`: Add unit tests for schema validator UI, orphan inspector UI, doctor UI, schema drift analyzer UI, Lint All dashboard.
  - Target: Maintain 100% test passing rate and high (>90%) coverage across all new modules.

---

## 7. Recommendations for Implementation Phases

1. **Phase 2 - Milestone M1 (Subprocess & UI Primitives)**:
   - Extend `BMClient` in `src/bmh/core/client.py` with all required methods.
   - Update `src/bmh/ui/cards.py` to integrate observation badge formatting in note cards, and add helper renderers for diagnostic outputs.
2. **Phase 2 - Milestone M2 (Ingest Hub)**:
   - Create `src/bmh/workflows/ingest.py`.
   - Implement structured templates (Task, Insight, Meeting, Decision, Scratchpad) generating canonical YAML frontmatter.
   - Implement observation appender and piped capture handler.
3. **Phase 2 - Milestone M3 (Query Hub & Co-Pilot)**:
   - Create `src/bmh/workflows/query.py`.
   - Implement active task step checkoff (reading task, toggling `[ ]` to `[x]`, calling `client.edit_note`).
   - Implement detail note reader and Guided Query Co-Pilot interview workflow.
4. **Phase 2 - Milestone M4 (Lint Hub & Health Diagnostics)**:
   - Create `src/bmh/workflows/lint.py`.
   - Implement interactive runners and Rich display tables for schema validation, orphans, doctor, schema drift, and Lint All dashboard.
5. **Phase 2 - Milestone M5 (Gateway & Navigation)**:
   - Restructure `src/bmh/ui/menu.py` to host the Tri-Modal Hub menu.
   - Wire top-level menu options `[1] Ingest`, `[2] Query`, `[3] Lint`, `[4] Update`, `[0] Exit` to respective workflow hubs.
   - Verify piped stdin handling in `src/bmh/main.py`.
6. **Phase 3 - Hardening & Verification**:
   - Verify 100% passing tests with `uv run pytest`.
   - Verify installation with `uv tool install . --force`.
