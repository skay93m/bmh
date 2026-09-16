# Original User Request

## 2026-09-15T23:18:32Z

Implement the Tri-Modal (Ingest, Query, Lint) interactive CLI architecture for `bmh` (Basic Memory Helper), an interactive Python CLI companion for Basic Memory (`bm`).

Working directory: /Users/kancil/.bmh
Integrity mode: development

## Requirements

### R1. Tri-Modal Interactive Gateway & Navigation
Restructure `bmh` into 3 top-level operational hubs:
1. `[1] 📥 Ingest` — Capture notes, structured templates, quick observation appender, and piped input.
2. `[2] 🔍 Query` — Search notes, active tasks, project browser, recent timeline, and the Guided Query Co-Pilot.
3. `[3] 🩺 Lint` — Schema validator, orphan link inspector, sync doctor, schema drift analyzer, and 'Lint All' health report.
Keep `[4] 🔄 Update` and `[0] 🚪 Exit`.

### R2. Ingest Hub (`src/bmh/workflows/ingest.py`)
Provide:
- **Interactive Note Capture Wizard** with structured templates (Task, Insight, Meeting, Decision, Scratchpad) generating canonical frontmatter and observations.
- **Quick Observation Appender**: Search or select an existing note and append tagged observations (`[decision]`, `[risk]`, `[insight]`, `[todo]`).
- **Piped Capture Handler**: Ingest raw markdown/text from stdin into target notes.

### R3. Query Hub & Guided Query Co-Pilot (`src/bmh/workflows/query.py`)
Provide:
- **Search & Task Browsers**: Keyword/title search, active task inspector with step checkoff, project explorer (`kancil`/`kensho`), recent activity timeline, and detail note reader.
- **Guided Query Co-Pilot**: An interactive interview workflow (akin to `/grill-me`) that guides the human user to clarify intent, formulates high-precision `bm` search queries, executes the retrieval, and presents rich card summaries.

### R4. Lint Hub & Health Diagnostics (`src/bmh/workflows/lint.py`)
Provide:
- **Schema Validator**: Validates note frontmatter and schemas using `bm tool schema-validate`.
- **Orphan & Broken Link Inspector**: Detects unlinked entities and dangling relations using `bm orphans`.
- **Sync & Index Doctor**: Verifies database indexing and consistency using `bm doctor`.
- **Schema Drift Analyzer**: Assesses drift between schema definitions and actual notes using `bm tool schema-diff`.
- **'Lint All' Dashboard**: Executes full diagnostic checkup and prints a formatted Rich summary.

### R5. Subprocess Execution & UI Consistency
- Core subprocess primitives in `src/bmh/core/client.py` for all `bm` commands (`search-notes`, `write-note`, `edit-note`, `schema-validate`, `schema-diff`, `doctor`, `orphans`).
- Rich panel formatting with syntax-highlighted Markdown and observation badges in `src/bmh/ui/cards.py`.

## Acceptance Criteria

### Navigation & Gateway
- [ ] Running `bmh` launches the top-level Tri-Modal menu with Ingest, Query, Lint, Update, and Exit options.
- [ ] Piped input (`... | bmh`) formats incoming JSON stream into Rich cards.
- [ ] Subprocess errors and missing `bm` binaries are handled gracefully without uncaught tracebacks.

### Ingest Workflow
- [ ] Interactive wizards create valid markdown notes for all 5 templates (Task, Insight, Meeting, Decision, Scratchpad) via `bm tool write-note`.
- [ ] Observation appender appends tagged observations to selected notes via `bm tool edit-note`.

### Query Workflow
- [ ] Note search, task discovery, project browsing, and recent notes display formatted Rich cards.
- [ ] Guided Query Co-Pilot interactively asks clarifying questions, generates a search query, and displays results.

### Lint Workflow
- [ ] Schema validation, orphan detection, doctor checks, and schema drift run through `bm` CLI and display structured Rich reports.
- [ ] "Lint All" executes all checks and produces a unified health score/summary.

### Testing & Verification
- [ ] All new modules covered by comprehensive `pytest` test suite with 100% passing tests.
- [ ] `uv run pytest` and `uv tool install . --force` succeed without errors.
