# Specification Mining Report: Tri-Modal Interactive CLI Architecture for `bmh`
**Role**: Survey Spec Miner 1  
**Project**: `bmh` (Basic Memory Helper)  
**Date**: 2026-09-15 / 2026-09-16  
**Status**: Authoritative & Complete  
**Reference Sources**: `ORIGINAL_REQUEST.md`, live host `bm` CLI (`/Users/kancil/.local/bin/bm`), codebase at `/Users/kancil/.bmh`

---

## 1. Executive Summary & Architecture Overview

`bmh` (Basic Memory Helper) is an interactive Python CLI companion for **Basic Memory** (`bm`). It transforms the CLI experience from manual flag memorization and raw JSON parsing into a guided, structured terminal console.

The goal of this architectural milestone is the implementation of the **Tri-Modal Architecture**, organizing all operations into three primary operational hubs:
1. **`[1] 📥 Ingest Hub`**: Interactive note capture wizards with 5 canonical templates (`Task`, `Insight`, `Meeting`, `Decision`, `Scratchpad`), quick observation appender, and piped text capture.
2. **`[2] 🔍 Query Hub & Guided Query Co-Pilot`**: Multi-dimensional search, active task inspection with interactive checkbox checkoff (`[ ]` -> `[x]`), project explorer (`kancil`/`kensho`), recent activity timeline, detail note reader, and an interactive `/grill-me`-style Guided Query Co-Pilot.
3. **`[3] 🩺 Lint Hub & Health Diagnostics`**: Frontmatter schema validator, orphan and broken link inspector, database sync & index doctor, schema drift analyzer, and a unified 'Lint All' health dashboard with automated scoring and grading.
4. **`[4] 🔄 Update`**: Multi-environment updater engine (`git`, `uv tool`, `pipx`).
5. **`[0] 🚪 Exit`**: Clean termination with zero uncaught exceptions.

All operations execute through deterministic, robust subprocess primitives (`src/bmh/core/client.py`) wrapping `bm`, rendering high-signal Rich panels and cards (`src/bmh/ui/cards.py`) with observation badge styling (`[decision]`, `[risk]`, `[insight]`, `[todo]`, `[status]`).

---

## 2. Exhaustive Requirements Breakdown

### R1. Tri-Modal Interactive Gateway & Navigation

#### 1.1 Top-Level Menu Gateway
- **Entrypoint**: `bmh` launched without subcommands in a TTY terminal (`sys.stdin.isatty() == True`).
- **Banner**: Displays standard branded banner (`render_banner()`).
- **Hub Selection**:
  ```text
  What would you like to do?
    [1] 📥 Ingest (capture notes, templates, observations, piped data)
    [2] 🔍 Query (search, active tasks, project browser, timeline, co-pilot)
    [3] 🩺 Lint (schemas, orphans, doctor, drift, lint all)
    [4] 🔄 Update bmh (pull latest release)
    [0] 🚪 Exit
  ```
- **Navigation Invariants**:
  - Accepts numeric keys (`1`, `2`, `3`, `4`, `0`) and natural aliases (`ingest`, `query`, `lint`, `update`, `exit`, `q`, `quit`).
  - Submenu operations return cleanly to the hub menu or the top-level gateway.
  - Gracefully captures `KeyboardInterrupt` (`Ctrl+C`) and `EOFError` (`Ctrl+D`) displaying `\n[dim]Goodbye![/dim]\n` with exit code 0.

#### 1.2 Stdin Stream Detection & Piped Card Formatter
- **Non-TTY Input**: When data is piped via stdin (`not sys.stdin.isatty()`):
  - **Structured JSON**: Parses JSON arrays, objects, or envelopes (`results`, `items`, `notes`, `data`, `rows`) into `List[NoteModel]` using `normalize_notes_json(input_data)`.
  - **Rendering**: Formats and outputs structured Rich panels (`render_note_cards(notes)`).
  - **Fallback**: If raw text or non-JSON text is piped without an ingest command, falls back to a plain text note card `NoteModel(title="Plain Text Output", content=data)`.
  - **Empty Stdin**: If piped input is empty or whitespace only, emits `\n[yellow]No input provided on stdin.[/yellow]\n` without tracebacks.

#### 1.3 Subprocess & Binary Error Shielding
- Any subprocess invocation verifying `BMClient.is_available()`:
  - If binary not found, raises `BMNotFoundError` and displays a user-friendly Rich panel explaining missing `bm` binary and how to resolve it.
  - If `bm` returns a non-zero exit code, raises `BMExecutionError` containing `exit_code`, `stderr`, and `stdout`, caught by `_handle_client_error` to display a clean red diagnostic message rather than a Python traceback.

---

### R2. Ingest Hub (`src/bmh/workflows/ingest.py`)

#### 2.1 Hub Submenu Structure
```text
── 📥 Ingest Hub ──
  [1] 📝 Interactive Note Capture Wizard (5 Structured Templates)
  [2] 🏷️  Quick Observation Appender
  [3] 📋 Piped Capture Handler
  [0] ⬅️  Back to Main Menu
```

#### 2.2 Interactive Note Capture Wizard (5 Structured Templates)
Guides the operator through structured prompts, builds canonical YAML frontmatter and standard markdown sections, and persists the note via `client.write_note(...)`.

##### Template 1: `Task`
- **Target Folder**: `tasks/` (or user specified)
- **Prompts**:
  1. Title (e.g. `Implement OAuth2 Token Refresh`)
  2. Description / Problem statement
  3. Status (`active`, `planned`, `blocked`, `completed`; default: `active`)
  4. Priority (`high`, `medium`, `low`; default: `medium`)
  5. Assignee (e.g. `louis`, `kancil`, or blank)
  6. Steps (multiline or comma/sequential prompt: step 1, step 2, etc.)
  7. Project target (`kancil`, `kensho`, or default)
  8. Tags (comma-separated, e.g. `auth, backend`)
  9. Related notes (relations, e.g. `[[Auth Service Design]]`)
- **Canonical Output Schema**:
  ```markdown
  ---
  title: Implement OAuth2 Token Refresh
  type: task
  status: active
  priority: medium
  tags: [auth, backend]
  assigned_to: louis
  ---
  # Implement OAuth2 Token Refresh

  Implement automatic token refreshing when JWT expires.

  ## Observations
  - [description] Implement automatic token refreshing when JWT expires.
  - [status] active
  - [priority] medium
  - [assigned_to] louis

  ## Steps
  1. [ ] Inspect expired token response in middleware
  2. [ ] Issue refresh token request to identity provider
  3. [ ] Store updated credentials securely

  ## Context
  Standard OAuth2 refresh token workflow for API clients.

  ## Relations
  - relates_to [[Auth Service Design]]
  ```

##### Template 2: `Insight`
- **Target Folder**: `insights/` (or `knowledge/`)
- **Prompts**:
  1. Title
  2. Core finding / synthesis
  3. Key observation / takeaway
  4. Downstream implications / impact
  5. Tags (comma-separated)
  6. Related notes
- **Canonical Output Schema**:
  ```markdown
  ---
  title: Vector Hybrid Retrieval Latency Bottleneck
  type: insight
  tags: [performance, vector, search]
  ---
  # Vector Hybrid Retrieval Latency Bottleneck

  Analysis of search performance across high-cardinality collections.

  ## Observations
  - [insight] Unfiltered vector retrieval takes 80% of query latency on datasets >10k notes.
  - [implication] Frontmatter metadata pre-filtering must precede vector similarity calculations.

  ## Context / Evidence
  Observed during benchmarking of SQLite FTS5 vs vector cosine similarity.

  ## Relations
  - relates_to [[Search Engine Architecture]]
  ```

##### Template 3: `Meeting`
- **Target Folder**: `meetings/` (or `notes/`)
- **Prompts**:
  1. Title (e.g. `Sprint Planning 2026-09-16`)
  2. Date (default: today `YYYY-MM-DD`)
  3. Participants (comma-separated)
  4. Discussion summary / Agenda
  5. Key decisions made (`[decision]`)
  6. Identified risks (`[risk]`)
  7. Action items / Todos (`[todo]` + step checkboxes)
- **Canonical Output Schema**:
  ```markdown
  ---
  title: Sprint Planning 2026-09-16
  type: meeting
  date: 2026-09-16
  participants: [syafiq, louis]
  tags: [sprint, planning]
  ---
  # Sprint Planning 2026-09-16

  ## Agenda & Discussion
  Reviewed Q3 roadmap deliverables and prioritised Tri-Modal CLI rollout.

  ## Observations
  - [decision] Deploy Tri-Modal architecture under develop branch before release tagging.
  - [risk] Subprocess timeouts during large doctor runs must be bounded to 30 seconds.
  - [todo] Finalise unit tests for ingest and query hubs.

  ## Action Items
  1. [ ] Implement client subprocess primitives
  2. [ ] Verify schema validation across all notes

  ## Relations
  - relates_to [[Roadmap 2026]]
  ```

##### Template 4: `Decision`
- **Target Folder**: `decisions/`
- **Prompts**:
  1. Title (e.g. `Adopt Pydantic v2 for Subprocess Data Contracts`)
  2. Status (`proposed`, `decided`, `superseded`; default: `decided`)
  3. Context / Problem Statement
  4. Decision taken (`[decision]`)
  5. Rationale & Trade-offs (`[rationale]`)
  6. Accepted Risks (`[risk]`)
  7. Consequences & Relations
- **Canonical Output Schema**:
  ```markdown
  ---
  title: Adopt Pydantic v2 for Subprocess Data Contracts
  type: decision
  status: decided
  date: 2026-09-16
  tags: [architecture, python, validation]
  ---
  # Adopt Pydantic v2 for Subprocess Data Contracts

  ## Context & Problem Statement
  Subprocess JSON outputs from `bm` require resilient, strict schema validation.

  ## Observations
  - [decision] Standardise all bmh internal representations on Pydantic BaseModel with validators.
  - [rationale] Pydantic v2 provides high performance, type coercion, and schema evolution handling.
  - [risk] Extra schema maintenance required when bm upstream JSON output changes.

  ## Consequences
  Enables graceful degradation and structured card rendering.

  ## Relations
  - governed_by [[BMH Architecture Guidelines]]
  ```

##### Template 5: `Scratchpad`
- **Target Folder**: `scratchpad/` (or `inbox/`)
- **Prompts**:
  1. Title (e.g. `Temporary API Notes`)
  2. Freeform body text (multiline)
  3. Tags (default: `[scratchpad, draft]`)
- **Canonical Output Schema**:
  ```markdown
  ---
  title: Temporary API Notes
  type: scratchpad
  date: 2026-09-16
  tags: [scratchpad, draft]
  ---
  # Temporary API Notes

  Raw notes and snippets captured during exploration.

  ## Observations
  - [todo] Triage and organise into permanent notes.
  ```

#### 2.3 Quick Observation Appender
- **Objective**: Append observation badges directly to any existing note without requiring an editor.
- **Workflow**:
  1. **Select Note**: User enters search term or picks from recently accessed notes.
  2. **Note Matcher**: If multiple notes match, displays numbered selection table with Title, Entity/Permalink, and File Path.
  3. **Select Tag**: User chooses from standard observation tags:
     - `[1] [decision]` (green)
     - `[2] [risk]` (red)
     - `[3] [insight]` (magenta)
     - `[4] [todo]` (yellow)
     - `[5] Custom tag` (user entered, e.g. `[status]`, `[constraint]`)
  4. **Input Observation**: User enters text content.
  5. **Execution**: Formulates `- [<tag>] <text>\n` and executes `client.edit_note(identifier=note.permalink or note.title, operation="append", content=f"\n- [{tag}] {text}\n", project=project)`.
  6. **Feedback**: Displays confirmation panel with rendered observation badge and note permalink.

#### 2.4 Piped Capture Handler
- **Objective**: Ingest raw markdown or plain text streams into target notes.
- **Interactive Flow**:
  1. Detects raw text input or prompts user for multiline paste (until empty line / EOF).
  2. Asks whether to create a **New Note** or **Append to Existing Note**.
  3. If **New Note**: Prompts for Title, Folder (default `inbox/`), and Project. Calls `client.write_note(...)`.
  4. If **Append**: Prompts for Target Note (title/permalink), calls `client.edit_note(..., operation="append")`.
  5. Displays resulting Rich card confirmation.

---

### R3. Query Hub & Guided Query Co-Pilot (`src/bmh/workflows/query.py`)

#### 3.1 Hub Submenu Structure
```text
── 🔍 Query Hub ──
  [1] 🔍 Search Notes (by query, title, tag, status, project)
  [2] ⚡ Active Tasks Inspector & Step Checkoff
  [3] 📚 Browse by Project (kancil / kensho / all)
  [4] 🕒 Recent Activity Timeline
  [5] 📖 Detail Note Reader
  [6] 🤖 Guided Query Co-Pilot (interactive interview)
  [0] ⬅️  Back to Main Menu
```

#### 3.2 Search Browser
- **Prompts**:
  - Search query string (optional if filters provided)
  - Search in title only? (Y/n)
  - Project filter (`kancil`, `kensho`, or all)
  - Note type filter (`task`, `decision`, `insight`, `meeting`, etc.)
  - Tag filter
- **Retrieval**: Calls `client.search_notes(query, project, note_type, is_title, ...)`.
- **Display**: Renders compact, high-density Rich cards (`render_note_cards`) showing headers, styled observation badges, checkboxes, and metadata footers.

#### 3.3 Active Task Inspector & Step Checkoff
- **Retrieval**: Executes `client.search_notes(note_type="task", status="active", project=project)`.
- **Task Selection**: Displays active tasks in a numbered menu showing title, assignee, and updated timestamp.
- **Step Parser**: Scans task markdown content for checklist steps:
  - Matches regex `r"^(?:(\d+\.)|[-*])\s+\[([ xX])\]\s+(.*)$"`
  - Distinguishes checked steps (`☑`) from unchecked steps (`☐`).
- **Interactive Checkoff**:
  - Displays all steps with numeric indices.
  - Prompts user: "Select step number to check off (or 0 to cancel)".
  - On selection, replaces `[ ] <step_text>` with `[x] <step_text>`.
  - Executes `client.edit_note(identifier, operation="find_replace", find_text=f"[ ] {step_text}", content=f"[x] {step_text}", project=project)`.
  - Displays updated step panel: `[bold green]✓ Step checked off successfully![/bold green]`.

#### 3.4 Project Explorer
- **Available Projects**: Queries `client.list_projects()` dynamically or offers primary projects (`kancil`, `kensho`).
- **Description Mapping**:
  - `kancil`: Operational life, active projects, agent workflows.
  - `kensho`: Durable knowledge base, reference architectures, permanent notes.
- **Action**: Lets user browse by type, list all notes, or search within the selected project.

#### 3.5 Recent Activity Timeline
- **Retrieval**: Executes `client.recent_activity(timeframe="7d", project=project)` or `client.search_notes(after_date="7d", project=project)`.
- **Presentation**: Formats a chronological Rich timeline table:
  - Timestamp (formatted `DD/MM/YY HH:MM`)
  - Title & Type badge
  - Entity permalink
  - Brief snippet or observation highlight

#### 3.6 Detail Note Reader
- **Input**: Note title, permalink, or numeric selection from previous search.
- **Retrieval**: Executes `client.read_note(identifier, project=project, frontmatter=True)`.
- **Display**: Renders full-width Rich Panel:
  - Full title and metadata header
  - Syntax-highlighted Markdown body
  - Colored observation badges (`[decision]`, `[risk]`, `[insight]`, `[todo]`, `[status]`)
  - Styled checkboxes (`☑`, `☐`)
  - Footers with path, entity, external ID, and relation links.

#### 3.7 Guided Query Co-Pilot (Interactive Interview)
The Guided Query Co-Pilot is an interactive interview workflow (inspired by `/grill-me`) that guides the human operator to clarify intent, construct high-precision queries, execute retrieval, and format summaries:
1. **Interview Step 1 (Intent Clarification)**:
   - "What are you looking for or trying to accomplish?"
   - Examples: "Finding an architecture decision", "Checking task status", "Reviewing meeting notes", "Investigating a bug or defect".
2. **Interview Step 2 (Domain & Scope)**:
   - "Which project workspace should we search?"
   - Options: `kancil` (operational), `kensho` (durable reference), or `all`.
3. **Interview Step 3 (Knowledge Type)**:
   - "What type of artifact are you looking for?"
   - Options: `All types`, `Tasks`, `Decisions`, `Insights`, `Meetings`, `Specifications`.
4. **Interview Step 4 (Time Horizon)**:
   - "What timeframe is relevant?"
   - Options: `Anytime`, `Past 24 hours (1d)`, `Past week (7d)`, `Past month (30d)`.
5. **Interview Step 5 (Key Terms & Entities)**:
   - "Any specific keywords, filenames, or linked entities?"
6. **Synthesis & Query Formulation**:
   - The Co-Pilot synthesizes answers into exact `bm tool search-notes` parameters:
     - `query`: sanitized keywords or phrase
     - `project`: selected project
     - `note_type`: selected type
     - `after_date`: timeframe parameter
   - Renders a **Query Synthesis Card**:
     ```text
     ╭────────────── 🤖 Guided Query Co-Pilot ──────────────╮
     │ Formulated High-Precision Query:                     │
     │   • Query: "oauth2 refresh"                          │
     │   • Project: kancil                                  │
     │   • Type: task                                       │
     │   • Timeframe: 7d                                    │
     ╰──────────────────────────────────────────────────────╯
     ```
7. **Execution & Card Presentation**:
   - Prompts: "Execute search? [Y/n]".
   - Calls `client.search_notes(...)`.
   - Renders retrieved notes as formatted Rich cards.
   - Provides summary metrics: total matches found, precision filters applied.

---

### R4. Lint Hub & Health Diagnostics (`src/bmh/workflows/lint.py`)

#### 4.1 Hub Submenu Structure
```text
── 🩺 Lint Hub & Health Diagnostics ──
  [1] 📐 Schema Validator (bm tool schema-validate)
  [2] 🔗 Orphan & Broken Link Inspector (bm orphans)
  [3] 🩺 Sync & Index Doctor (bm doctor)
  [4] 📊 Schema Drift Analyzer (bm tool schema-diff)
  [5] 🏆 'Lint All' Health Dashboard (full diagnostic checkup)
  [0] ⬅️  Back to Main Menu
```

#### 4.2 Schema Validator
- **Subprocess Command**: `bm tool schema-validate [target] [--project project]`
- **JSON Contract**:
  - `total_notes`: int
  - `valid_count`: int
  - `warning_count`: int
  - `error_count`: int
  - `results`: list of objects:
    - `note_identifier`: str
    - `schema_entity`: str
    - `passed`: bool
    - `warnings`: list of str
    - `errors`: list of str
    - `field_results`: list of field status items (`field_name`, `status`: present/missing, `required`: bool, `message`: str)
- **UI Presentation**:
  - Rich Table: Columns `Note`, `Schema`, `Status` (green `PASS`, yellow `WARN`, red `FAIL`), `Issues`.
  - Issue Details: Sub-table or bullet list highlighting required missing fields (`Missing required field: description`).
  - Summary footer: `X/Y valid, W warnings, E errors`.

#### 4.3 Orphan & Broken Link Inspector
- **Subprocess Command**: `bm orphans --json [--project project]`
- **JSON Contract**:
  - List of objects: `[{"external_id": str, "title": str, "note_type": str, "file_path": str}]`
- **UI Presentation**:
  - Total Orphan Count header badge.
  - Rich Table: Columns `#`, `Title`, `Type`, `File Path`, `External ID`.
  - Explanatory footnote: "Orphan entities have no incoming or outgoing connections in the knowledge graph. Consider linking them or reviewing."
  - Empty case: If 0 orphans, displays `[bold green]✨ Knowledge graph clean: No orphan entities found![/bold green]`.

#### 4.4 Sync & Index Doctor
- **Subprocess Command**: `bm doctor [--project project]`
- **Output Contract**:
  - Lines containing `OK <check description>` or failure messages.
  - Final line: `Doctor checks passed.` or failure description.
- **UI Presentation**:
  - Rich Panel with structured check list:
    - `[green]✓[/green] Created doctor project`
    - `[green]✓[/green] API write created file`
    - `[green]✓[/green] Manual file written`
    - `[green]✓[/green] Project index processed manual file`
    - `[green]✓[/green] Search confirmed manual file`
    - `[green]✓[/green] Status observed indexed file`
  - Overall status indicator: `[bold green]🩺 Doctor Status: Healthy & Synced[/bold green]`.

#### 4.5 Schema Drift Analyzer
- **Subprocess Command**: `bm tool schema-diff <note_type> [--project project]`
- **JSON Contract**:
  - `note_type`: str
  - `schema_found`: bool
  - `new_fields`: list of `{name: str, source: str, count: int, total: int, percentage: float}`
  - `dropped_fields`: list of `{name: str, source: str, count: int, total: int, percentage: float}`
  - `cardinality_changes`: list
- **UI Presentation**:
  - Note Type Header: `Schema Drift Analysis: <note_type>`
  - Rich Table for **New Fields** (fields present in notes but missing from schema): Name, Source (`observation`/`relation`), Occurrence Count / Percentage.
  - Rich Table for **Dropped/Unused Fields** (fields declared in schema but unused in notes): Name, Missing Percentage.
  - Empty case: If drift is empty, displays `[bold green]✨ Perfect Alignment: No schema drift detected for note type '<note_type>'[/bold green]`.

#### 4.6 'Lint All' Health Dashboard & Scoring Rubric
Executes all four diagnostic modules in sequence and aggregates results into a unified health score (0–100%) and Grade:
- **Scoring Rubric (100 Points Total)**:
  1. **Sync & Doctor (30 points)**:
     - Doctor passed: 30 pts.
     - Doctor failed: 0 pts.
  2. **Schema Validation (40 points)**:
     - Calculated as: `40 * (valid_count / total_notes) - (error_count * 10) - (warning_count * 2)`. Min: 0 pts.
  3. **Graph Connectivity / Orphans (20 points)**:
     - Calculated based on orphan ratio: `20 * max(0.0, 1.0 - (orphan_count / max(total_notes, 1)))`. Min: 0 pts.
  4. **Schema Stability & Drift (10 points)**:
     - 10 pts if no drift; deducted proportionally per drifted field. Min: 0 pts.
- **Letter Grades**:
  - **90–100%**: Grade A (Excellent - Fully Indexed & Connected)
  - **75–89%**: Grade B (Good - Minor warnings or unlinked notes)
  - **60–74%**: Grade C (Fair - Needs schema cleanup or link pruning)
  - **<60%**: Grade F (Poor - Sync failure or multiple schema errors)
- **UI Presentation**:
  - Rich Panel with large Score Badge: e.g. `[bold green]Overall Health Score: 92/100 (GRADE A)[/bold green]`
  - Diagnostics Grid / Summary Table:
    - Doctor: PASS
    - Schema: Valid (X/Y notes, W warnings, E errors)
    - Orphans: N entities unlinked
    - Schema Drift: D fields drifting
  - Prioritised Action Items list (e.g. `1. Add [description] observation to TASK-020`, `2. Link 5 orphan notes in knowledge/`).

---

### R5. Subprocess Execution & UI Consistency

#### 5.1 Subprocess Primitives (`src/bmh/core/client.py`)
All interactions with `bm` must go through typed methods on `BMClient`:
1. `search_notes(...) -> List[NoteModel]`: Runs `tool search-notes`.
2. `write_note(title: str, folder: str, content: str, tags: Optional[List[str]] = None, note_type: Optional[str] = None, project: Optional[str] = None, overwrite: bool = False) -> subprocess.CompletedProcess`: Runs `tool write-note`.
3. `edit_note(identifier: str, operation: str, content: str, find_text: Optional[str] = None, section: Optional[str] = None, project: Optional[str] = None) -> subprocess.CompletedProcess`: Runs `tool edit-note`.
4. `read_note(identifier: str, project: Optional[str] = None, frontmatter: bool = True) -> NoteModel`: Runs `tool read-note --json`.
5. `recent_activity(timeframe: str = "7d", item_type: Optional[str] = None, project: Optional[str] = None, page_size: int = 10) -> List[Dict[str, Any]]`: Runs `tool recent-activity --json`.
6. `list_projects() -> Dict[str, Any]`: Runs `tool list-projects`.
7. `schema_validate(target: Optional[str] = None, project: Optional[str] = None) -> Dict[str, Any]`: Runs `tool schema-validate`.
8. `schema_diff(note_type: str, project: Optional[str] = None) -> Dict[str, Any]`: Runs `tool schema-diff`.
9. `doctor() -> Dict[str, Any]`: Runs `doctor`.
10. `orphans(project: Optional[str] = None) -> List[Dict[str, Any]]`: Runs `orphans --json`.

#### 5.2 UI Rendering & Formatting (`src/bmh/ui/cards.py`)
- **Card Anatomy**:
  - **Header**: `📌 <Title> [Index/Total]`
  - **Body**: Formatted Rich Markdown or Rich Text with styled observation badges:
    - `[decision]` -> `[bold green]\[decision][/bold green]`
    - `[insight]` -> `[bold magenta]\[insight][/bold magenta]`
    - `[risk]` -> `[bold red]\[risk][/bold red]`
    - `[todo]` -> `[bold yellow]\[todo][/bold yellow]`
    - `[status]` -> `[bold blue]\[status][/bold blue]`
    - Checkboxes: `[x]` -> `[green]☑[/green]`, `[ ]` -> `[dim]☐[/dim]`
  - **Footer**: `entity: <permalink> | external_id: <uuid> | file: <path> | updated: <date>`
  - **Borders & Colors**: Cyan border (`border_style="cyan"`), left-aligned title, left-aligned subtitle.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Gateway (R1) | Tri-Modal Top-Level Menu | Top-level interactive menu dispatching to Ingest, Query, Lint, Update, and Exit | Menu selection string/digit (`1`-`4`, `0`, aliases) | Submenu invocation or program exit | Re-prompts on invalid input; clean exit on `q`/`Ctrl+C` | `ORIGINAL_REQUEST.md`, `src/bmh/ui/menu.py` |
| 2 | Gateway (R1) | Piped JSON Stream Formatter | Ingests JSON streams on stdin and renders structured Rich cards | Piped JSON string via stdin (`sys.stdin.read()`) | Rendered Rich note panels | Falls back to plain text note card on malformed JSON; warns on empty input | `ORIGINAL_REQUEST.md`, `src/bmh/main.py` |
| 3 | Gateway (R1) | Subprocess Binary Guard | Verifies existence of `bm` CLI executable | PATH lookup (`shutil.which`) or `BM_PATH` | Boolean availability | Raises `BMNotFoundError`, caught by UI to print actionable install guide | `src/bmh/core/client.py` |
| 4 | Ingest (R2) | Ingest Hub Submenu | Dedicated submenu for note capture, observation appending, and piped capture | User selection (`1`-`3`, `0`) | Sub-flow execution or return to main menu | Re-prompts on invalid choice; returns on `0` | `ORIGINAL_REQUEST.md` R2 |
| 5 | Ingest (R2) | Task Note Template Wizard | Interactive wizard generating canonical Task frontmatter and observation sections | Title, description, status, priority, assignee, steps, project | Created task note written via `bm tool write-note` | Re-prompts on missing required fields; handles write conflicts via `--overwrite` | `ORIGINAL_REQUEST.md` R2, live `bm` schemas |
| 6 | Ingest (R2) | Insight Note Template Wizard | Interactive wizard generating canonical Insight frontmatter and observations | Title, finding, insight, implication, tags, project | Created insight note written via `bm tool write-note` | Validates non-empty title; handles write failure gracefully | `ORIGINAL_REQUEST.md` R2 |
| 7 | Ingest (R2) | Meeting Note Template Wizard | Interactive wizard generating canonical Meeting frontmatter, decisions, risks, and action items | Title, date, participants, agenda, decisions, risks, action items | Created meeting note written via `bm tool write-note` | Validates date format (defaults to current date); handles subprocess errors | `ORIGINAL_REQUEST.md` R2 |
| 8 | Ingest (R2) | Decision Note Template Wizard | Interactive wizard generating canonical Decision frontmatter, rationale, and consequences | Title, status, context, decision, rationale, risks, relations | Created decision note written via `bm tool write-note` | Ensures valid decision status; reports write errors | `ORIGINAL_REQUEST.md` R2 |
| 9 | Ingest (R2) | Scratchpad Note Wizard | Quick capture wizard for unstructured notes and temporary drafts | Title, content body, optional tags | Created scratchpad note written via `bm tool write-note` | Defaults title if empty; handles write errors | `ORIGINAL_REQUEST.md` R2 |
| 10 | Ingest (R2) | Quick Observation Appender | Search/select existing note and append tagged observations (`[decision]`, `[risk]`, `[insight]`, `[todo]`) | Note selector, tag choice, observation text | Appended observation line via `bm tool edit-note --operation append` | Shows warning if note not found; reports edit failures | `ORIGINAL_REQUEST.md` R2, `bm tool edit-note` |
| 11 | Ingest (R2) | Piped / Multiline Text Capture | Captures raw markdown or stdin stream and directs into new or existing note | Raw text input, destination choice (new vs existing note), folder/note identifier | Note written or appended via `client.write_note` or `client.edit_note` | Warns if empty text provided; reports write failures | `ORIGINAL_REQUEST.md` R2 |
| 12 | Query (R3) | Query Hub Submenu | Dedicated navigation menu for all retrieval, browsing, inspection, and co-pilot flows | User selection (`1`-`6`, `0`) | Flow invocation or return to main menu | Re-prompts on invalid input; clean return on `0` | `ORIGINAL_REQUEST.md` R3 |
| 13 | Query (R3) | Filtered Note Search Browser | Keyword, title, tag, type, and project note search | Query string, title boolean, project, note type, tag | Formatted Rich cards via `render_note_cards` | Prints yellow warning if 0 matches; catches search syntax errors | `ORIGINAL_REQUEST.md` R3, `src/bmh/ui/menu.py` |
| 14 | Query (R3) | Active Tasks Inspector | Displays active commitments and project tasks | Project filter (`kancil`, `kensho`, or all) | Formatted task cards with status and step indicators | Warns if no active tasks found | `ORIGINAL_REQUEST.md` R3, `src/bmh/ui/menu.py` |
| 15 | Query (R3) | Interactive Task Step Checkoff | Parses task checklist items and allows interactive completion (`[ ]` -> `[x]`) | Task selection, step index | In-place note update via `bm tool edit-note --operation find_replace` | Warns if task has no steps or if all steps already completed | `ORIGINAL_REQUEST.md` R3, `ROADMAP.md` STORY-006 |
| 16 | Query (R3) | Project Knowledge Browser | Explores notes within scoped knowledge bases (`kancil`, `kensho`) | Project choice (`1`/`2`), optional search query | Formatted note cards scoped to project | Validates project choice; reports retrieval errors | `ORIGINAL_REQUEST.md` R3, `src/bmh/ui/menu.py` |
| 17 | Query (R3) | Recent Activity Timeline | Retrieves and displays chronological activity across the knowledge base | Timeframe (`7d`, `30d`), project filter | Chronological Rich table with timestamps, titles, and paths | Handles empty timeframe results cleanly | `ORIGINAL_REQUEST.md` R3, `bm tool recent-activity` |
| 18 | Query (R3) | Detail Note Reader / Pager | Inspects full note content with Rich syntax highlighting and observation badges | Note identifier (permalink, title, or search selection) | Full-screen Rich panel card with formatted markdown | Displays error panel if note not found | `ORIGINAL_REQUEST.md` R3, `ROADMAP.md` STORY-008 |
| 19 | Query (R3) | Guided Query Co-Pilot | Interactive interview workflow clarifying intent, constructing high-precision queries, and presenting summaries | Multi-step user prompts (intent, scope, type, timeframe, keywords) | Synthesized query preview, executed search results, card summaries | Re-prompts on invalid interview selections; offers fallback if no results | `ORIGINAL_REQUEST.md` R3 |
| 20 | Lint (R4) | Lint Hub Submenu | Submenu for schema validation, orphans, doctor checks, drift, and dashboard | User selection (`1`-`5`, `0`) | Sub-check invocation or return to main menu | Re-prompts on invalid input; clean return on `0` | `ORIGINAL_REQUEST.md` R4 |
| 21 | Lint (R4) | Schema Validator | Validates note frontmatter and field schemas via `bm tool schema-validate` | Target note or note type (optional), project | Rich table displaying note name, status (`PASS`/`WARN`/`FAIL`), warnings, errors | Highlights missing required vs optional fields cleanly | `ORIGINAL_REQUEST.md` R4, `bm tool schema-validate` |
| 22 | Lint (R4) | Orphan Link Inspector | Detects unlinked entities and dangling relations via `bm orphans --json` | Project filter | Rich table of orphan notes (title, type, path, external_id) | Displays congratulatory badge if 0 orphans found | `ORIGINAL_REQUEST.md` R4, `bm orphans` |
| 23 | Lint (R4) | Sync & Index Doctor | Executes local consistency checks via `bm doctor` | Project (optional) | Rich panel with itemized check statuses and overall pass/fail status | Displays red panel with failure explanation if doctor fails | `ORIGINAL_REQUEST.md` R4, `bm doctor` |
| 24 | Lint (R4) | Schema Drift Analyzer | Analyzes divergence between schema definitions and note usage via `bm tool schema-diff` | Note type (`Task`, `Conversation`, etc.), project | Rich table of added fields, dropped fields, and usage percentages | Informs user if schema not found or if 0 drift detected | `ORIGINAL_REQUEST.md` R4, `bm tool schema-diff` |
| 25 | Lint (R4) | 'Lint All' Health Dashboard | Executes all 4 diagnostics in sequence, calculates health score and grade | Project (optional) | Unified Rich dashboard with 0-100 score, letter grade, summary table, recommendations | Aggregates partial failures into score penalty without crashing | `ORIGINAL_REQUEST.md` R4 |
| 26 | Client (R5) | `write_note` Subprocess Primitive | Programmatic execution of `bm tool write-note` | `title`, `folder`, `content`, `tags`, `type`, `project`, `overwrite` | `subprocess.CompletedProcess` | Raises `BMExecutionError` on non-zero exit | `ORIGINAL_REQUEST.md` R5, `bm tool write-note` |
| 27 | Client (R5) | `edit_note` Subprocess Primitive | Programmatic execution of `bm tool edit-note` | `identifier`, `operation`, `content`, `find_text`, `section`, `project` | `subprocess.CompletedProcess` | Raises `BMExecutionError` on non-zero exit | `ORIGINAL_REQUEST.md` R5, `bm tool edit-note` |
| 28 | Client (R5) | `read_note` Subprocess Primitive | Programmatic execution of `bm tool read-note --json` | `identifier`, `project`, `frontmatter` | `NoteModel` | Raises `BMExecutionError` if note does not exist | `ORIGINAL_REQUEST.md` R5, `bm tool read-note` |
| 29 | Client (R5) | `schema_validate` Subprocess Primitive | Programmatic execution of `bm tool schema-validate` | `target`, `project` | Parsed JSON dict (`total_notes`, `valid_count`, `results`) | Raises `BMExecutionError` or `json.JSONDecodeError` | `ORIGINAL_REQUEST.md` R5, `bm tool schema-validate` |
| 30 | Client (R5) | `schema_diff` Subprocess Primitive | Programmatic execution of `bm tool schema-diff` | `note_type`, `project` | Parsed JSON dict (`new_fields`, `dropped_fields`) | Raises `BMExecutionError` on failure | `ORIGINAL_REQUEST.md` R5, `bm tool schema-diff` |
| 31 | Client (R5) | `doctor` Subprocess Primitive | Programmatic execution of `bm doctor` | Project (optional) | Parsed result dict (`passed`, `output`, `checks`) | Returns `passed=False` on check failures | `ORIGINAL_REQUEST.md` R5, `bm doctor` |
| 32 | Client (R5) | `orphans` Subprocess Primitive | Programmatic execution of `bm orphans --json` | Project (optional) | Parsed list of dicts | Raises `BMExecutionError` on non-zero exit | `ORIGINAL_REQUEST.md` R5, `bm orphans` |
| 33 | Client (R5) | `recent_activity` Subprocess Primitive | Programmatic execution of `bm tool recent-activity --json` | `timeframe`, `item_type`, `project`, `page_size` | Parsed list of activity dicts | Raises `BMExecutionError` on failure | `bm tool recent-activity` |
| 34 | Client (R5) | `list_projects` Subprocess Primitive | Programmatic execution of `bm tool list-projects` | None | Parsed project catalog dict | Raises `BMExecutionError` on failure | `bm tool list-projects` |
| 35 | UI (R5) | Observation Badges Formatter | Formats inline observation tags into high-contrast colored markup | Note content string | Formatted string / Rich renderable with highlighted badges | Escapes brackets properly to prevent markup parsing errors | `src/bmh/ui/cards.py`, `AGENTS.md` |
| 36 | UI (R5) | Step Checkbox Formatter | Formats `[ ]` and `[x]` into styled unicode checkboxes (`☐`, `☑`) | Note content string | Formatted string / Rich renderable with styled checkboxes | Handles mixed cases (`[X]`, `[x]`, `[ ]`) | `src/bmh/ui/cards.py`, `AGENTS.md` |
| 37 | Updater (R1) | Self-Update Engine | Checks and applies updates across git, `uv tool`, or `pipx` | User trigger (`4` in menu or `bmh update`) | Execution of update command with status spinner | Prints manual upgrade command if environment unrecognized | `src/bmh/updater/engine.py` |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | `BMClient.execute` | Missing `bm` binary in PATH | Raises `BMNotFoundError`; caught by UI handler to display clean help message without Python traceback. |
| 2 | `BMClient.search_notes` | No query, no filters provided | `bm tool search-notes` exits with code 1 ("Please provide at least one of: `query`, `metadata_filters`..."); caught by client and rendered as clear error message. |
| 3 | `BMClient.search_notes` | Wildcard query `*` without filters | `bm tool search-notes` exits with code 1 ("Hybrid retrieval requires a non-empty text query..."); caught and explained to user. |
| 4 | `render_note_cards` | Empty search results `[]` | Outputs `\n[yellow]No notes found matching criteria.[/yellow]\n`. |
| 5 | Stdin piped mode | Empty string `""` or whitespace on stdin | Outputs `\n[yellow]No input provided on stdin.[/yellow]\n` and terminates with code 0. |
| 6 | Stdin piped mode | Plain unformatted text (not JSON) | `normalize_notes_json` wraps text into a single `NoteModel(title="Plain Text Output", content=data)` and displays card. |
| 7 | Stdin piped mode | Malformed JSON string | JSON parser catches error, safely falls back to plain text note card without crashing. |
| 8 | Ingest: Template Wizard | Empty required title input | Wizard re-prompts: "Title is required. Please enter a title:". |
| 9 | Ingest: Write Note | Existing note conflict without overwrite | `bm tool write-note` returns conflict error; wizard catches error and prompts: "Note already exists. Overwrite? [y/N]". |
| 10 | Ingest: Appender | Search returns 0 matching notes | Displays `[yellow]No notes found matching query.[/yellow]` and prompts user to re-enter search or return to menu. |
| 11 | Ingest: Appender | Note content lacks `## Observations` header | Appender safely appends observation line at end of note content; `bm` indexes tagged line regardless of section. |
| 12 | Query: Task Step Checkoff | Task has no checklist steps (`[ ]` or `[x]`) | Displays `[yellow]No checklist steps found in this task note.[/yellow]` and returns to task menu. |
| 13 | Query: Task Step Checkoff | All steps already checked off (`[x]`) | Displays `[bold green]All checklist steps are already completed! (☑)[/bold green]` and returns. |
| 14 | Query: Task Step Checkoff | Multiple identical step strings | Finds and replaces the selected step instance specifically. |
| 15 | Lint: Schema Validator | Note has schema warnings but 0 errors | Displays yellow `WARN` badge and lists missing optional observations (e.g. `[context]`, `[steps]`). |
| 16 | Lint: Schema Validator | Target note has no schema definition | Returns 0 schema errors; indicates note is unconstrained. |
| 17 | Lint: Orphan Inspector | Zero orphans found | Displays `[bold green]✨ Knowledge graph clean: No orphan entities found![/bold green]`. |
| 18 | Lint: Schema Drift | Note type does not exist | `bm tool schema-diff` returns `"schema_found": false`; displays warning that schema definition does not exist. |
| 19 | Lint: Schema Drift | Schema has 0 new fields and 0 dropped fields | Displays `[bold green]✨ Perfect Alignment: No schema drift detected.[/bold green]`. |
| 20 | Lint: 'Lint All' | Doctor command fails or times out | Health score docks 30 points; dashboard still completes and renders remaining checks with Grade penalty. |
| 21 | Interactive Navigation | User presses `Ctrl+C` or `Ctrl+D` at any prompt | Prompt catches `KeyboardInterrupt`/`EOFError`, prints `\n[dim]Goodbye![/dim]\n` and exits with code 0. |
| 22 | Interactive Navigation | User types invalid choice (e.g. `foo`, `99`) | Reprompts user without crashing. |

---

## 5. Acceptance Criteria Mapping

| Acceptance Criterion | Verification Method | Expected Behavior |
|----------------------|---------------------|-------------------|
| **AC-1: Gateway Tri-Modal Menu** | Run `bmh` in terminal; inspect displayed options | Launches banner + top-level menu with `[1] Ingest`, `[2] Query`, `[3] Lint`, `[4] Update`, `[0] Exit`. |
| **AC-2: Piped Input Card Formatter** | Run `bm tool search-notes --type task --json \| bmh` | Parses incoming JSON stream, normalizes envelopes, and renders Rich panels with title, content, badges, and footer. |
| **AC-3: Subprocess Error Shielding** | Run `bmh` with `BM_PATH=/nonexistent/bm`; simulate CLI failures | Displays formatted Rich red error panel without raw Python stack traces or uncaught exceptions. |
| **AC-4: Ingest 5 Templates** | Run Ingest wizard for Task, Insight, Meeting, Decision, Scratchpad | Prompts user for fields, creates valid markdown with frontmatter and observations, invokes `bm tool write-note`, outputs success card. |
| **AC-5: Observation Appender** | Select existing note and append `[decision]`, `[risk]`, `[insight]`, or `[todo]` | Modifies note via `bm tool edit-note --operation append`, adds tagged line, displays updated card. |
| **AC-6: Query Browsers & Detail** | Run note search, active tasks, project browse, recent activity | Executes queries via `BMClient`, renders results in compact Rich cards, allows selecting a note for detail reading. |
| **AC-7: Task Step Checkoff** | Open active task in Task Inspector, select step to complete | Toggles `[ ]` to `[x]` via `bm tool edit-note --operation find_replace`, re-renders updated steps. |
| **AC-8: Guided Query Co-Pilot** | Complete multi-step Co-Pilot interview (intent, scope, type, timeframe) | Formulates precise `bm tool search-notes` command, shows query card preview, executes search, presents results. |
| **AC-9: Lint Diagnostics** | Execute Schema Validator, Orphan Inspector, Doctor, and Drift Analyzer | Executes respective `bm` CLI commands (`schema-validate`, `orphans`, `doctor`, `schema-diff`) and renders formatted Rich tables/panels. |
| **AC-10: 'Lint All' Dashboard** | Run 'Lint All' checkup from Lint Hub | Executes all 4 diagnostics sequentially, computes unified health score (0-100%) and Grade (A-F), renders unified summary dashboard. |
| **AC-11: 100% Passing Pytest Suite** | Run `uv run pytest` | All existing (60) and new unit tests pass with zero errors and high test coverage. |
| **AC-12: Installation Verification** | Run `uv tool install . --force` | Package installs cleanly as standalone CLI executable without dependency or build errors. |

---

## 6. Data Contracts & Subprocess Specifications

### 6.1 `BMClient` Core Primitives Specification (`src/bmh/core/client.py`)

```python
class BMClient:
    def __init__(self, binary_path: Optional[str] = None): ...
    def is_available(self) -> bool: ...
    def execute(self, args: List[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]: ...

    # 1. Search Notes
    def search_notes(
        self,
        query: Optional[str] = None,
        project: Optional[str] = None,
        note_type: Optional[str] = None,
        status: Optional[str] = None,
        is_title: bool = False,
        tags: Optional[List[str]] = None,
        after_date: Optional[str] = None,
        entity_type: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> List[NoteModel]: ...

    # 2. Write Note
    def write_note(
        self,
        title: str,
        folder: str,
        content: str,
        tags: Optional[List[str]] = None,
        note_type: Optional[str] = None,
        project: Optional[str] = None,
        overwrite: bool = False,
    ) -> subprocess.CompletedProcess[str]: ...

    # 3. Edit Note
    def edit_note(
        self,
        identifier: str,
        operation: str,  # 'append' | 'prepend' | 'find_replace' | 'replace_section'
        content: str,
        find_text: Optional[str] = None,
        section: Optional[str] = None,
        project: Optional[str] = None,
    ) -> subprocess.CompletedProcess[str]: ...

    # 4. Read Note
    def read_note(
        self,
        identifier: str,
        project: Optional[str] = None,
        frontmatter: bool = True,
    ) -> NoteModel: ...

    # 5. Recent Activity
    def recent_activity(
        self,
        timeframe: str = "7d",
        item_type: Optional[str] = None,
        project: Optional[str] = None,
        page_size: int = 10,
    ) -> List[Dict[str, Any]]: ...

    # 6. List Projects
    def list_projects(self) -> Dict[str, Any]: ...

    # 7. Schema Validate
    def schema_validate(
        self,
        target: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Dict[str, Any]: ...

    # 8. Schema Diff
    def schema_diff(
        self,
        note_type: str,
        project: Optional[str] = None,
    ) -> Dict[str, Any]: ...

    # 9. Doctor
    def doctor(self) -> Dict[str, Any]: ...

    # 10. Orphans
    def orphans(
        self,
        project: Optional[str] = None,
    ) -> List[Dict[str, Any]]: ...
```

---

## 7. Testing & Verification Plan

### 7.1 Test Structure & Modules
1. **`tests/test_client.py`**:
   - Test `write_note`: verifies CLI arguments `["tool", "write-note", "--title", ...]` and flags.
   - Test `edit_note`: verifies operations (`append`, `find_replace`, etc.).
   - Test `read_note`: verifies parsing into `NoteModel`.
   - Test `schema_validate`: verifies JSON decoding and mock error handling.
   - Test `schema_diff`: verifies parsing of drift outputs.
   - Test `doctor`: verifies parsing of `OK ...` lines and return dictionary.
   - Test `orphans`: verifies parsing of JSON list of orphans.
   - Test error handling: verifies `BMNotFoundError` and `BMExecutionError` triggers.
2. **`tests/test_cards.py`**:
   - Test observation badge formatting (`[decision]`, `[risk]`, `[insight]`, `[todo]`, `[status]`).
   - Test checkbox formatting (`[ ]` -> `☐`, `[x]` -> `☑`).
   - Test panel headers, footers, subtitles, date formatters.
3. **`tests/test_ingest.py`**:
   - Test all 5 template generators (`Task`, `Insight`, `Meeting`, `Decision`, `Scratchpad`).
   - Test frontmatter YAML validity and required fields.
   - Test observation appender logic.
   - Test piped capture handler.
4. **`tests/test_query.py`**:
   - Test search browser filters.
   - Test task step parser (regex matching of numbered and bullet checkboxes).
   - Test step checkoff execution (`find_replace` invocation).
   - Test Guided Query Co-Pilot interview logic, query builder, and synthesis card.
5. **`tests/test_lint.py`**:
   - Test schema validation table rendering.
   - Test orphan inspector empty and non-empty rendering.
   - Test doctor check panel formatting.
   - Test schema drift diff table formatting.
   - Test 'Lint All' scoring algorithm and Grade assignment (A, B, C, D, F).
6. **`tests/test_menu.py`**:
   - Test top-level Tri-Modal menu loop (`1: Ingest`, `2: Query`, `3: Lint`, `4: Update`, `0: Exit`).
   - Test hub dispatching and clean return to main menu.
7. **`tests/test_main.py`**:
   - Test stdin piped JSON formatting vs interactive launch.
   - Test graceful exit on `KeyboardInterrupt` and `EOFError`.

### 7.2 Verification Commands
```bash
# Run unit test suite
uv run pytest -v

# Run unit tests with coverage
uv run pytest --cov=src/bmh --cov-report=term-missing

# Test local editable install
uv tool install . --force

# Verify help and version
uv run bmh --version
uv run bmh --help
```

---

## 8. Conclusion & Handoff Summary
This specification report provides an exhaustive, unambiguous blueprint for the Tri-Modal CLI architecture for `bmh`. All requirements (R1–R5), user interaction workflows, data models, subprocess command signatures, error conditions, edge cases, and verification criteria have been mined directly from the authoritative specification and verified against the live host environment.
