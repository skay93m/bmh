# Comprehensive Survey Report: `bm` CLI Environment, Commands, and Interfaces

**Author:** Survey Explorer 2  
**Date:** 2026-09-15 / 2026-09-16  
**Target Project:** `bmh` (Basic Memory Helper) Tri-Modal Interactive CLI  
**Working Directory:** `/Users/kancil/.bmh/.agents/survey_explorer_2`

---

## 1. Executive Summary & Environment Overview

### 1.1 Binary & Runtime Environment
- **Binary Path:** `/Users/kancil/.local/bin/bm`
- **Installation Method:** Python script executable installed via `uv tool install basic-memory`
- **Python Environment:** `/Users/kancil/.local/share/uv/tools/basic-memory/bin/python` (Python 3.12.9)
- **Package Location:** `/Users/kancil/.local/share/uv/tools/basic-memory/lib/python3.12/site-packages/basic_memory`
- **Installed Version:** `Basic Memory version: 0.23.2`
- **CLI Framework:** Typer / Click with Rich styling and Loguru logging

### 1.2 System & Project Context
Running `bm tool list-projects` against the local environment revealed the active projects registered on this machine:
1. `kancil` (Path: `/Users/kancil/kancil`, Default project: `true`, Source: `local+cloud`)
2. `kensho` (Path: `/Users/kancil/kensho`, Default project: `false`, Source: `local+cloud`)
3. `main` (Path: `/Users/kancil/basic-memory`, Source: `local+cloud`)
4. `getting-started` (Path: `/getting-started`, Source: `cloud`)
5. `doctor-1e3b566b` (Path: `/Users/kancil/kensho/doctor-1e3b566b`, Source: `local`)
6. `openclaw-kancil-node` (Path: `/Users/kancil/.openclaw/workspace`, Source: `local`)

Default project fallback is `kancil`. The presence of both `kancil` and `kensho` directly satisfies R3's project browser requirement.

---

## 2. Command Signatures, Arguments, and Outputs

### 2.1 `bm doctor`
**Purpose:** Verifies local consistency between file storage and database indexing.
- **Invocation:** `bm doctor [OPTIONS]`
- **Options:**
  - `--local`: Force local API routing (default in doctor check)
  - `--cloud`: Force cloud API routing
  - `--help`: Display help
- **Behavior & Output Format:**
  - `bm doctor` does **NOT** accept a `--json` flag. It writes Rich-formatted status text to stdout.
  - Generates an ephemeral doctor project (e.g. `doctor-b8b4f0de`), creates an entity via API, verifies file on disk, creates a manual markdown file directly, triggers indexer, queries search client, checks status client, and cleans up the temporary project.
  - Success Output:
    ```text
    Running Basic Memory doctor checks...
    OK Created doctor project: doctor-b8b4f0de
    OK API write created file
    OK Manual file written
    OK Project index processed manual file
    OK Search confirmed manual file
    OK Status observed indexed file
    Doctor checks passed.
    ```
  - Exit code on success: `0`
  - Exit code on failure: `1`, with console message `Doctor failed: <reason>`

### 2.2 `bm orphans`
**Purpose:** Discovers graph entities that have no relations (neither incoming nor outgoing links).
- **Invocation:** `bm orphans [OPTIONS]`
- **Options:**
  - `--project <str>`: Target project name (defaults to active/default project, e.g., `kancil`)
  - `--json`: Output results in JSON format
  - `--local`: Force local API routing
  - `--cloud`: Force cloud API routing
  - `--help`: Display help
- **Output Formats:**
  - **Terminal / Default Mode:** Rich table titled `<project>: Entities Without Relations (<count> total)` with columns: `Title`, `File Path`, `Type`.
  - **JSON Mode (`--json`):** Pure JSON array of node items:
    ```json
    [
      {
        "external_id": "e07bad16-42ad-4725-83e0-c21fa9061e36",
        "title": "architecture",
        "note_type": "note",
        "file_path": "architecture/architecture.md"
      }
    ]
    ```
  - If no orphans exist: In text mode prints `No orphan entities in project '<project>'`. In JSON mode outputs `[]`.
- **Error Behavior:**
  - If project does not exist: exits with code `1`.
  - If `--json` was passed: prints JSON error payload to stdout:
    ```json
    {
      "error": "Project not found: 'invalid-project'"
    }
    ```
  - If `--json` not passed: prints `[red]Error: Project not found: ...[/red]` to stderr/console.

---

### 2.3 `bm tool search-notes`
**Purpose:** Primary search engine across notes, metadata, frontmatter, and embeddings.
- **Invocation:** `bm tool search-notes [OPTIONS] [query]`
- **Arguments:**
  - `query`: Optional search query string (optional if metadata/tag filters are supplied).
- **Options:**
  - `--title`: Search in title values only
  - `--permalink`: Search permalink values only
  - `--vector`: Force vector retrieval
  - `--hybrid`: Force hybrid retrieval (BM25 + vector)
  - `--tag <str>`: Filter by frontmatter tag (repeatable)
  - `--status <str>`: Filter by frontmatter status (e.g. `active`, `done`, `draft`)
  - `--type <str>`: Filter by frontmatter note type (e.g. `task`, `note`, `guide`, `decision`)
  - `--entity-type <str>`: Filter by item type: `entity`, `observation`, `relation` (repeatable)
  - `--category <str>`: Filter observation results to exact categories (e.g. `decision`, `risk`, `todo`)
  - `--meta <str>`: Filter by frontmatter `key=value` (repeatable)
  - `--filter <str>`: Advanced JSON metadata filter
  - `--page <int>`: Page number [default: 1]
  - `--page-size <int>`: Page size [default: 10]
  - `--project <str>`: Project name
  - `--project-id <str>`: Project UUID external_id
  - `--json`: Output raw JSON
  - `--plain`: Output undecorated plain text
  - `--local`, `--cloud`: Routing overrides
- **Output JSON Envelope (`--json` or non-TTY piped):**
  ```json
  {
    "results": [
      {
        "title": "Daily Token Spend Optimisation",
        "type": "entity",
        "score": 0.88,
        "entity": "kancil/tasks/daily-token-spend-optimisation",
        "external_id": "8ff93f44-fdd2-4290-958c-75176432f8d1",
        "permalink": "kancil/tasks/daily-token-spend-optimisation",
        "content": "# Daily Token Spend Optimisation\n\n...",
        "matched_chunk": "## Steps\n1. [x] ...",
        "file_path": "tasks/daily-token-spend-optimisation.md",
        "updated_at": "2026-09-15T05:10:58.065171Z",
        "metadata": {
          "note_type": "task"
        },
        "entity_id": 1579
      }
    ],
    "current_page": 1,
    "page_size": 10,
    "total": 2,
    "total_is_exact": true,
    "has_more": false
  }
  ```
- **Error Behavior & Validation:**
  - **No Search Criteria Guard:** If called with no query AND no filter flags, command exits with **exit code 1** and writes:
    `# No Search Criteria\nPlease provide at least one of: query, metadata_filters, tags, status, note_types, entity_types, categories, or after_date.`
  - When no results match: exits code `0`, returns `"results": []`, `"total": 0`.

---

### 2.4 `bm tool write-note`
**Purpose:** Creates a new note or completely replaces an existing note.
- **Invocation:** `bm tool write-note [OPTIONS]`
- **Options:**
  - `--title <str>` [Required]: Title of the note.
  - `--folder <str>` [Required]: Destination folder relative to project root (e.g., `tasks`, `notes`, `inbox`).
  - `--content <str>` [Optional]: Note content. If omitted, reads from stdin!
  - `--tags <str>` [Optional]: Comma-separated or whitespace tags.
  - `--type <str>` [Optional, default: `"note"`]: Note type in frontmatter (e.g. `task`, `insight`, `meeting`, `decision`, `scratchpad`).
  - `--project <str>`: Target project.
  - `--overwrite`: Flag to overwrite an existing note if title/permalink conflicts.
  - `--local`, `--cloud`: Routing overrides.
- **Stdin Input Handling:**
  - Supports piped capture: `cat draft.md | bm tool write-note --title "Draft" --folder "inbox"`
  - If content is not provided and stdin is a TTY: exits with **code 1**, stderr:
    `No content provided. Please provide content via --content or by piping to stdin.`
  - If content is empty or whitespace: exits with **code 1**, stderr:
    `Empty content provided. Please provide non-empty content.`
- **Success JSON Output:**
  ```json
  {
    "title": "My Note",
    "permalink": "kancil/notes/my-note",
    "file_path": "notes/my-note.md",
    "checksum": "a1b2c3d4...",
    "action": "created"
  }
  ```
- **Conflict / Error Handling:**
  - If note exists and `--overwrite` is NOT passed:
    - Exit code: **`1`**
    - Stderr: `Error: NOTE_ALREADY_EXISTS`
    - Stdout:
      ```json
      {
        "title": "My Note",
        "permalink": "kancil/notes/my-note",
        "file_path": null,
        "checksum": null,
        "action": "conflict",
        "error": "NOTE_ALREADY_EXISTS"
      }
      ```

---

### 2.5 `bm tool edit-note`
**Purpose:** Performs granular modifications to an existing note without overwriting entire file.
- **Invocation:** `bm tool edit-note [OPTIONS] {identifier}`
- **Arguments:**
  - `identifier` [Required]: Permalink (e.g., `kancil/tasks/task-020`) or file path (e.g., `tasks/task-020.md`).
- **Options:**
  - `--operation <str>` [Required]: One of:
    1. `append`: Append content to end of note.
    2. `prepend`: Prepend content to beginning of note (below frontmatter).
    3. `find_replace`: Find text and replace it.
    4. `replace_section`: Replace the body of a markdown heading.
  - `--content <str>` [Required]: Content to append/prepend/insert.
  - `--find-text <str>`: Target substring for `find_replace`.
  - `--section <str>`: Target section heading for `replace_section` (e.g., `"## Observations"`).
  - `--expected-replacements <int>` [Default: `1`]: Validation count for `find_replace`.
  - `--replace-subsections` / `--no-replace-subsections` [Default: `replace-subsections`].
  - `--project <str>`: Target project.
- **Success JSON Output:**
  ```json
  {
    "title": "Daily Token Spend Optimisation",
    "permalink": "kancil/tasks/daily-token-spend-optimisation",
    "file_path": "tasks/daily-token-spend-optimisation.md",
    "checksum": "f8a9b2...",
    "operation": "append",
    "fileCreated": false
  }
  ```
- **Error Handling:**
  - If identifier does not resolve to any note or find_text is missing:
    - Exit code: **`1`**
    - Stderr: `Error: <error message>`
    - Stdout:
      ```json
      {
        "title": null,
        "permalink": null,
        "file_path": null,
        "checksum": null,
        "operation": "append",
        "fileCreated": false,
        "error": "<error message>"
      }
      ```

---

### 2.6 `bm tool read-note`
**Purpose:** Reads the content and frontmatter of a note by title, permalink, or file path.
- **Invocation:** `bm tool read-note [OPTIONS] {identifier}`
- **Options:**
  - `--frontmatter` / `--include-frontmatter`: Include YAML frontmatter in output.
  - `--json`: Force JSON output.
  - `--plain`: Undecorated text.
  - `--project <str>`: Target project.
- **Success JSON Output:**
  ```json
  {
    "title": "Daily Token Spend Optimisation",
    "permalink": "kancil/tasks/daily-token-spend-optimisation",
    "file_path": "tasks/daily-token-spend-optimisation.md",
    "content": "# Daily Token Spend Optimisation\n\n...",
    "frontmatter": {
      "title": "Daily Token Spend Optimisation",
      "type": "task",
      "permalink": "kancil/tasks/daily-token-spend-optimisation",
      "status": "active",
      "priority": "high",
      "assigned_to": "louis",
      "current_step": 4,
      "steps": [
        "Establish token and context baseline from session metadata",
        "Activate deterministic command automation for recurring measurements"
      ],
      "tags": ["task", "finance"]
    }
  }
  ```
- **Critical Edge Case — Note Not Found:**
  - Unlike `write-note` or `edit-note`, `bm tool read-note "nonexistent"` exits with **exit code 0**!
  - Output payload:
    ```json
    {
      "title": null,
      "permalink": null,
      "file_path": null,
      "content": null,
      "frontmatter": null
    }
    ```
  - **Implication for `BMClient`:** The client must verify `result.get("content") is not None` or `result.get("title") is not None` to verify note existence, rather than relying solely on `returncode == 0`.

---

### 2.7 `bm tool schema-validate`
**Purpose:** Validates note schemas and frontmatter attributes.
- **Invocation:** `bm tool schema-validate [OPTIONS] [target]`
- **Arguments:**
  - `target` [Optional]: Specific note path (e.g. `tasks/task-020.md`) or note type (e.g. `Task`). If omitted, validates all schemas in the project.
- **Options:**
  - `--project <str>`: Target project.
  - `--local`, `--cloud`: Routing overrides.
- **Output:** **Always outputs pure JSON** (no `--json` flag required).
- **JSON Structure:**
  ```json
  {
    "total_notes": 2,
    "total_entities": 2,
    "valid_count": 2,
    "warning_count": 1,
    "error_count": 0,
    "results": [
      {
        "note_identifier": "TASK-020 Basic Memory OpenClaw Integration Repair",
        "schema_entity": "Task",
        "passed": true,
        "field_results": [
          {
            "field_name": "description",
            "field_type": "string",
            "required": true,
            "status": "missing",
            "values": [],
            "message": "Missing required field: description (expected [description] observation)"
          }
        ],
        "unmatched_observations": {},
        "unmatched_relations": [],
        "warnings": ["Missing required field: description ..."],
        "errors": []
      }
    ],
    "type_summaries": [
      {
        "note_type": "Task",
        "total_notes": 2,
        "total_entities": 2,
        "valid_count": 2,
        "warning_count": 1,
        "error_count": 0
      }
    ]
  }
  ```
- **Error Behavior:**
  - If a target type does not exist (e.g., `bm tool schema-validate nonexistent`): exits code **`0`** with:
    ```json
    {
      "error": "No notes found of type 'nonexistent'"
    }
    ```

---

### 2.8 `bm tool schema-diff`
**Purpose:** Detects schema drift between defined schemas and actual field usage across notes.
- **Invocation:** `bm tool schema-diff [OPTIONS] {note_type}`
- **Arguments:**
  - `note_type` [Required]: Schema type name (e.g., `Task`, `Conversation`).
- **Options:**
  - `--project <str>`: Target project.
- **Output:** **Always outputs pure JSON** (no `--json` flag required).
- **Success JSON Structure:**
  ```json
  {
    "note_type": "Task",
    "schema_found": true,
    "new_fields": [
      {
        "name": "cadence",
        "source": "observation",
        "count": 1,
        "total": 2,
        "percentage": 0.5
      }
    ],
    "dropped_fields": [
      {
        "name": "steps",
        "source": "observation",
        "count": 0,
        "total": 2,
        "percentage": 0.0
      }
    ],
    "cardinality_changes": []
  }
  ```
- **Edge Case (No Schema Found):**
  - If note type has no schema: exits with code **`0`**!
  - Returns:
    ```json
    {
      "error": "No schema found for type 'nonexistent_type'"
    }
    ```

---

### 2.9 `bm tool list-projects` & `bm tool recent-activity`
- **`bm tool list-projects`:**
  - Outputs JSON directly.
  - Root keys: `"projects"` (array of project objects), `"default_project"` (string), `"constrained_project"`.
  - Each project object has: `name`, `external_id`, `path`, `local_path`, `cloud_path`, `source` (`"local+cloud"` or `"local"` or `"cloud"`), `is_default` (`bool`).
- **`bm tool recent-activity`:**
  - Accepts `--project`, `--page`, `--page-size`, `--json`.
  - Outputs JSON array of recent note activities:
    ```json
    [
      {
        "type": "entity",
        "title": "Basic Memory Deterministic Command Registry",
        "permalink": "kancil/operations/basic-memory-command-registry",
        "file_path": "operations/basic-memory-command-registry.md",
        "created_at": "2026-09-15T19:38:19.983525+00:00"
      }
    ]
    ```

---

## 3. Comparison Matrix: Subcommands & Error Modalities

| Command | Subcommand Path | Primary Output Mode | `--json` Flag Required? | Failure Exit Code | Error In JSON Payload? | Stderr Message |
|---|---|---|---|---|---|---|
| Search Notes | `bm tool search-notes` | Rich / Plain / JSON | Yes (or non-TTY) | `1` on missing criteria; `0` on empty | No (`results: []`) | Markdown text error if no criteria |
| Write Note | `bm tool write-note` | JSON | No (always JSON) | `1` on conflict/empty content | Yes (`error: "NOTE_ALREADY_EXISTS"`) | `Error: NOTE_ALREADY_EXISTS` |
| Edit Note | `bm tool edit-note` | JSON | No (always JSON) | `1` on missing target/param | Yes (`error: "..."`) | `Error: ...` |
| Read Note | `bm tool read-note` | Rich / Plain / JSON | Yes (or non-TTY) | `0` (even when not found!) | Values are `null` | None (clean stdout) |
| Schema Validate | `bm tool schema-validate` | JSON | No (always JSON) | `0` (even on unknown type!) | Yes (`error: "..."`) | None |
| Schema Diff | `bm tool schema-diff` | JSON | No (always JSON) | `0` (even on unknown type!) | Yes (`error: "..."`) | None |
| Doctor | `bm doctor` | Rich text / Plain | No JSON mode exists | `0` on pass, `1` on fail | N/A (Plain text only) | `Doctor failed: ...` |
| Orphans | `bm orphans` | Rich table / JSON | Yes (`--json`) | `0` on pass, `1` on error | Yes with `--json` | `[red]Error: ...[/red]` |
| List Projects | `bm tool list-projects` | JSON | No (always JSON) | `1` on failure | Yes | Stderr |
| Recent Activity | `bm tool recent-activity`| Rich / Plain / JSON | Yes (or non-TTY) | `0` | No | Stderr |

---

## 4. Key Observations & Design Recommendations for `bmh`

### 4.1 Subprocess Primitive Design (`src/bmh/core/client.py`)
1. **Stdin Streaming (`input` parameter):**
   Currently, `BMClient.execute(args, timeout)` does not take an `input: Optional[str] = None` argument.
   Adding `input: Optional[str] = None` to `execute()` and forwarding it to `subprocess.run(..., input=input)` is critical for:
   - `write-note` piped input (`content` via stdin).
   - Avoiding CLI argument buffer limits with large Markdown documents.
2. **Robust JSON Parsing & Exit Code 0 Error Guards:**
   Several `bm` commands exit with `returncode == 0` while returning an error structure:
   - `read-note`: Returns all `null`s when the note does not exist.
   - `schema-validate` & `schema-diff`: Return `{"error": "..."}` with exit code 0 when a type is missing.
   The client must inspect the decoded JSON dictionary for `"error"` keys and `null` identities and raise appropriate `BMError` or `BMNoteNotFoundError` exceptions.
3. **Structured Subprocess Methods Needed:**
   `BMClient` should expose dedicated high-level methods:
   - `search_notes(...) -> List[NoteModel]` (already present, refine parameters).
   - `read_note(identifier: str, project: Optional[str] = None) -> NoteModel`
   - `write_note(title: str, folder: str, content: str, note_type: str = "note", tags: Optional[List[str]] = None, overwrite: bool = False, project: Optional[str] = None) -> Dict[str, Any]`
   - `edit_note(identifier: str, operation: str, content: str, find_text: Optional[str] = None, section: Optional[str] = None, project: Optional[str] = None) -> Dict[str, Any]`
   - `list_projects() -> List[Dict[str, Any]]`
   - `get_recent_activity(page_size: int = 10, project: Optional[str] = None) -> List[Dict[str, Any]]`
   - `schema_validate(target: Optional[str] = None, project: Optional[str] = None) -> Dict[str, Any]`
   - `schema_diff(note_type: str, project: Optional[str] = None) -> Dict[str, Any]`
   - `doctor() -> Tuple[bool, str]`
   - `orphans(project: Optional[str] = None) -> List[Dict[str, Any]]`

### 4.2 Ingest Hub (`src/bmh/workflows/ingest.py`)
- **Note Templates:** 5 required templates (Task, Insight, Meeting, Decision, Scratchpad).
  - Can be written directly via `bm tool write-note --title <title> --folder <folder> --type <type>`.
  - Canonical observation syntax for frontmatter and body:
    - Task: `[description]`, `[status]`, `[assigned_to]`, `[current_step]`, `## Steps`.
    - Insight: `[insight]`, `[context]`, `[implication]`.
    - Meeting: `[attendees]`, `[agenda]`, `[action_item]`.
    - Decision: `[decision]`, `[context]`, `[consequence]`, `[status]`.
    - Scratchpad: `[scratchpad]`, `[tag]`.
- **Quick Observation Appender:**
  - Uses `bm tool edit-note <identifier> --operation append --content "- [<category>] <observation_text>"`.
  - Tagged categories: `[decision]`, `[risk]`, `[insight]`, `[todo]`.

### 4.3 Query Hub & Co-Pilot (`src/bmh/workflows/query.py`)
- **Projects:** Automatically list and switch between `kancil` and `kensho` using `bm tool list-projects`.
- **Active Tasks & Step Checkoff:**
  - Tasks can be retrieved via `bm tool search-notes --type task --json`.
  - Markdown step format in task content is `1. [ ] <step>` / `1. [x] <step>`.
  - Step checkoff can be executed via `bm tool edit-note <identifier> --operation find_replace --find-text "1. [ ] <step>" --content "1. [x] <step>"`.
- **Recent Timeline:**
  - Direct retrieval via `bm tool recent-activity --json`.
- **Guided Query Co-Pilot:**
  - Synthesizes user intent through prompt/questioning into high-precision flags: query string, `--type`, `--status`, `--tag`, `--project`.

### 4.4 Lint Hub (`src/bmh/workflows/lint.py`)
- **Schema Validator:** Calls `bm tool schema-validate` (returns `valid_count`, `warning_count`, `error_count`, `results`).
- **Orphan Inspector:** Calls `bm orphans --json` (returns list of unlinked nodes).
- **Sync Doctor:** Calls `bm doctor` (runs 7-step local consistency check).
- **Schema Drift:** Calls `bm tool schema-diff <type>` (returns `new_fields`, `dropped_fields`, `cardinality_changes`).
- **"Lint All" Health Dashboard:** Aggregates all four checks, computes a unified health score (e.g. ratio of clean schemas, low orphans, passed doctor checks), and displays a Rich summary table.

---

## 5. Verification Commands Run

All commands were verified live in this environment:
1. `which bm` → `/Users/kancil/.local/bin/bm` (exit code 0)
2. `bm --version` → `Basic Memory version: 0.23.2` (exit code 0)
3. `bm tool list-projects` → JSON with 6 projects, default `kancil` (exit code 0)
4. `bm doctor` → All 7 check stages passed: `Doctor checks passed.` (exit code 0)
5. `bm orphans --json` → JSON list of 112 unlinked entities in `kancil` (exit code 0)
6. `bm tool schema-validate` → JSON validation report: 2 notes, 2 valid, 1 warning (exit code 0)
7. `bm tool schema-diff Task` → JSON drift analysis: 5 new fields, 6 dropped fields (exit code 0)
8. `bm tool schema-diff nonexistent` → `{"error": "No schema found for type 'nonexistent'"}` (exit code 0)
9. `bm tool search-notes --type task --json` → JSON envelope with 2 task notes (exit code 0)
10. `bm tool search-notes --project kensho "a" --json --page-size 3` → JSON envelope with kensho notes (exit code 0)
11. `bm tool search-notes --project kensho --json` → Exit code 1, `# No Search Criteria` error
12. `bm tool read-note "tasks/daily-token-spend-optimisation.md" --json` → Full note JSON payload (exit code 0)
13. `bm tool read-note "nonexistent" --json` → `{"title": null, ...}` (exit code 0)
14. `bm orphans --project invalid --json` → Exit code 1, `{"error": "Project not found..."}`
15. `uv run pytest` → 60 passed in 0.42s in `/Users/kancil/.bmh`
