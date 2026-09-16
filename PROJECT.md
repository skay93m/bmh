# Project: bmh Tri-Modal CLI Architecture

## Architecture
- **CLI Framework**: Typer with Rich interactive TUI components.
- **Data Flow**:
  - `bmh.main`: CLI entry point, detects interactive TTY vs piped input (`sys.stdin.isatty()`). For piped input, routes to piped card renderer or piped note capture. For interactive TTY, renders banner and enters `run_gateway_menu()`.
  - `bmh.ui.menu`: Tri-Modal Gateway menu (`[1] Ingest`, `[2] Query`, `[3] Lint`, `[4] Update`, `[0] Exit`).
  - `bmh.workflows.ingest`: Note Capture Wizard (5 templates: Task, Insight, Meeting, Decision, Scratchpad), Quick Observation Appender, and Piped Capture Handler. Calls `BMClient.write_note` and `BMClient.edit_note`.
  - `bmh.workflows.query`: Search Notes, Active Task Inspector (with interactive step toggle), Project Browser (`kancil`/`kensho`), Recent Activity Timeline, Note Reader, and Guided Query Co-Pilot interview workflow. Calls `BMClient.search_notes`, `BMClient.read_note`, `BMClient.edit_note`, `BMClient.recent_activity`.
  - `bmh.workflows.lint`: Schema Validator, Orphan Link Inspector, Sync Doctor, Schema Drift Analyzer, and Unified 'Lint All' Dashboard. Calls `BMClient.schema_validate`, `BMClient.orphans`, `BMClient.doctor`, `BMClient.schema_diff`.
  - `bmh.core.client`: `BMClient` subprocess abstraction layer wrapping `/Users/kancil/.local/bin/bm`. Provides robust execution, error handling without uncaught tracebacks, stdin streaming support, and payload inspection.
  - `bmh.ui.cards`: Rich card rendering with Markdown body formatting, observation badge highlights (`[decision]`, `[risk]`, `[insight]`, `[todo]`, `[status]`), checklist status (`[x]`, `[ ]`), and diagnostic result panels.

## Code Layout
- `src/bmh/core/client.py` — Subprocess wrapper for all `bm` CLI commands (M1)
- `src/bmh/core/models.py` — Pydantic models for notes, tasks, search, lint results (M1)
- `src/bmh/ui/cards.py` — Rich panel, card, and observation badge formatting (M1)
- `src/bmh/workflows/ingest.py` — Note Capture Wizard, Quick Appender, Piped Ingest (M2)
- `src/bmh/workflows/query.py` — Search, Task Inspector, Project Explorer, Recent Timeline, Co-Pilot (M3)
- `src/bmh/workflows/lint.py` — Schema Validator, Orphans, Doctor, Schema Diff, Lint All (M4)
- `src/bmh/ui/menu.py` — Top-level Tri-Modal Hub navigation menu (M5)
- `src/bmh/main.py` — CLI entry point, piped JSON/text detection and gateway routing (M5)
- `tests/` — Test suites:
  - `tests/test_client.py` — Core client tests (M1)
  - `tests/test_cards.py` — UI card formatting and badge tests (M1)
  - `tests/test_ingest.py` — Ingest workflow tests (M2)
  - `tests/test_query.py` — Query workflow and Co-Pilot tests (M3)
  - `tests/test_lint.py` — Lint workflow and diagnostic tests (M4)
  - `tests/test_menu.py` — Gateway menu navigation tests (M5)
  - `tests/test_main.py` — CLI entry point and piped stream tests (M5)
  - `tests/e2e/` — Dual-track requirement-driven E2E tests (E2E Track & M6)

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | BMClient Subprocess Core | Typed wrappers for all 7+ `bm` CLI primitives with stdin streaming and error handling | M1 | R5 |
| 2 | Model Definitions | Pydantic models for Lint reports, Task checklists, Diff results, Ingest templates | M1 | R5 |
| 3 | Observation Badge Formatting | Render badges for `[decision]`, `[risk]`, `[insight]`, `[todo]`, `[status]`, `[x]`, `[ ]` | M1 | R5 |
| 4 | Diagnostic Result Panels | Rich panels and tables for schema validation, orphans, doctor, and drift | M1 | R5 |
| 5 | Task Note Template Wizard | Interactive wizard generating canonical Task frontmatter & body | M2 | R2 |
| 6 | Insight Note Template Wizard | Interactive wizard generating canonical Insight frontmatter & body | M2 | R2 |
| 7 | Meeting Note Template Wizard | Interactive wizard generating canonical Meeting frontmatter & body | M2 | R2 |
| 8 | Decision Note Template Wizard | Interactive wizard generating canonical Decision frontmatter & body | M2 | R2 |
| 9 | Scratchpad Note Template Wizard | Interactive wizard generating canonical Scratchpad frontmatter & body | M2 | R2 |
| 10 | Quick Observation Appender | Note search/select and append tagged observations | M2 | R2 |
| 11 | Piped Ingest Handler | Capture stdin text/markdown into target note via `bm tool write-note` | M2 | R2 |
| 12 | Note Search Browser | Interactive keyword/title search returning Rich note cards | M3 | R3 |
| 13 | Active Task Inspector | Filter and inspect active tasks with interactive step checkoff | M3 | R3 |
| 14 | Project Browser | Explore notes by canonical projects (`kancil`, `kensho`, etc.) | M3 | R3 |
| 15 | Recent Activity Timeline | Interactive timeline of recent note modifications | M3 | R3 |
| 16 | Detail Note Reader | Read and render full note markdown with Rich cards and observation badges | M3 | R3 |
| 17 | Guided Query Co-Pilot Interview | 5-step interactive interview to clarify user intent and formulate search | M3 | R3 |
| 18 | Co-Pilot Execution & Presentation | Execute formulated query, present results as Rich cards | M3 | R3 |
| 19 | Schema Validator Diagnostic | Validate note frontmatter and schema using `bm tool schema-validate` | M4 | R4 |
| 20 | Orphan Link Inspector | Detect unlinked entities and dangling relations using `bm orphans` | M4 | R4 |
| 21 | Sync & Index Doctor | Verify database indexing and consistency using `bm doctor` | M4 | R4 |
| 22 | Schema Drift Analyzer | Assess drift between schema definitions and notes using `bm tool schema-diff` | M4 | R4 |
| 23 | 'Lint All' Unified Dashboard | Run all diagnostic checks and output 100-point health score and summary | M4 | R4 |
| 24 | Tri-Modal Gateway Menu | Main menu: `[1] Ingest`, `[2] Query`, `[3] Lint`, `[4] Update`, `[0] Exit` | M5 | R1 |
| 25 | Piped JSON Stream Handling | Handle piped JSON streams (`... \| bmh`), format into Rich cards | M5 | R1 |
| 26 | Graceful Error Shielding | Shield missing binary or subprocess failures without uncaught tracebacks | M5 | R1 |
| 27 | Update & Exit Integration | Maintain updater invocation and clean interactive exit | M5 | R1 |
| 28 | E2E Test Suite Tiers 1-4 | Requirement-driven opaque-box test suite across all features | E2E Track | AC |
| 29 | 100% Pytest & Tool Install Verification | Pass full test suite and verify `uv tool install . --force` | M6 | AC |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Requirement-driven 4-tier opaque-box test suite publishing `TEST_READY.md` | none | IN_PROGRESS |
| 1 | Subprocess & UI Foundation | `BMClient` 7+ primitives, error shielding, stdin streaming, models, badge formatting | none | IN_PROGRESS |
| 2 | Ingest Hub | 5 template wizards, Quick Observation Appender, piped capture handler | M1 | PLANNED |
| 3 | Query Hub & Co-Pilot | Search, task inspector with checkoff, project browser, recent timeline, Co-Pilot | M1 | PLANNED |
| 4 | Lint Hub & Diagnostics | Schema validator, orphan inspector, sync doctor, drift analyzer, Lint All dashboard | M1 | PLANNED |
| 5 | Gateway & Navigation | Tri-Modal menu gateway, piped JSON stream renderer, update/exit integration | M2, M3, M4 | PLANNED |
| 6 | Final E2E Pass & Verification | Pass 100% tests, verify `uv tool install . --force`, adversarial coverage hardening | E2E, M5 | PLANNED |

## Interface Contracts

### `BMClient` (`src/bmh/core/client.py`)
```python
class BMClient:
    def __init__(self, bm_path: Optional[str] = None): ...
    def is_available(self) -> bool: ...
    def execute(self, args: list[str], timeout: int = 30, input: Optional[str] = None) -> subprocess.CompletedProcess: ...
    def search_notes(self, query: Optional[str] = None, project: Optional[str] = None, note_type: Optional[str] = None, status: Optional[str] = None, is_title: bool = False, json_output: bool = True) -> list[dict]: ...
    def write_note(self, title: str, folder: str, content: Optional[str] = None, tags: Optional[str] = None, note_type: Optional[str] = None, project: Optional[str] = None, overwrite: bool = False, input_content: Optional[str] = None) -> dict: ...
    def edit_note(self, identifier: str, operation: str, content: str, find_text: Optional[str] = None, section: Optional[str] = None, expected_replacements: int = 1, project: Optional[str] = None) -> dict: ...
    def read_note(self, identifier: str, project: Optional[str] = None) -> Optional[dict]: ...
    def schema_validate(self, target: Optional[str] = None, project: Optional[str] = None) -> dict: ...
    def schema_diff(self, note_type: str, project: Optional[str] = None) -> dict: ...
    def doctor(self) -> dict: ... # returns parsed status: {"status": "passed"|"failed", "output": str, "steps": list[str]}
    def orphans(self, project: Optional[str] = None) -> list[dict]: ...
    def recent_activity(self, page: int = 1, page_size: int = 10, project: Optional[str] = None) -> list[dict]: ...
    def list_projects(self) -> list[dict]: ...
```

### `ui/cards.py`
```python
def highlight_observations(content: str) -> str: ...
def render_note_card(note: NoteModel, console: Optional[Console] = None) -> Panel: ...
def render_schema_validation_panel(data: dict) -> Panel: ...
def render_orphan_list_panel(orphans: list[dict]) -> Panel: ...
def render_doctor_panel(data: dict) -> Panel: ...
def render_schema_diff_panel(data: dict) -> Panel: ...
def render_lint_all_dashboard(results: dict) -> Panel: ...
```

### Workflows Interface
- `ingest.run_ingest_hub(console, client)`: Sub-menu for Ingest (1: New Note Wizard, 2: Quick Observation Appender, 0: Back)
- `ingest.run_note_wizard(console, client, template_type=None)`: Interactive creation of 5 templates
- `ingest.run_quick_appender(console, client)`: Search/select note and append observation
- `ingest.handle_piped_capture(client, title=None, folder=None, note_type=None)`: Stdin ingest
- `query.run_query_hub(console, client)`: Sub-menu for Query (1: Search, 2: Active Tasks, 3: Project Browser, 4: Recent Activity, 5: Guided Co-Pilot, 0: Back)
- `query.run_guided_copilot(console, client)`: 5-step intent clarification interview and query execution
- `lint.run_lint_hub(console, client)`: Sub-menu for Lint (1: Schema Validate, 2: Orphans, 3: Doctor, 4: Schema Diff, 5: Lint All Dashboard, 0: Back)
- `lint.run_lint_all(console, client)`: Unified health report with 100-point score
- `menu.run_gateway_menu(console, client)`: Top-level Tri-Modal menu routing to Ingest, Query, Lint, Update, Exit
