# Handoff Report: Tri-Modal Interactive CLI Specification Mining

**Agent**: Survey Spec Miner 1  
**Working Directory**: `/Users/kancil/.bmh/.agents/survey_spec_miner_1`  
**Target File**: `/Users/kancil/.bmh/.agents/survey_spec_miner_1/report.md`  
**Parent Agent**: Orchestrator (`57c6f4a9-b4c0-4359-811c-65679aabc531`)  

---

## 1. Observation

1. **Host Environment & Executables**:
   - Python environment: Python 3.14.7 on macOS (`Darwin arm64`), managed by `uv`.
   - The authoritative `bm` CLI binary was discovered at `/Users/kancil/.local/bin/bm`.
   - Running `/Users/kancil/.local/bin/bm --help` confirmed commands: `status`, `reset`, `reindex`, `doctor`, `mcp`, `orphans`, `format`, `update`, `import`, `cloud`, `ci`, `man`, `tool`, `inspect`, `project`, `config`, `schema`, `hook`.
   - Running `/Users/kancil/.local/bin/bm tool --help` confirmed subcommands: `write-note`, `read-note`, `delete-note`, `edit-note`, `build-context`, `recent-activity`, `search-notes`, `list-projects`, `list-workspaces`, `schema-validate`, `schema-infer`, `schema-diff`.

2. **Subprocess Call Contracts & Real Outputs**:
   - Probing `bm tool write-note --help`: Requires `--title <str>` and `--folder <str>`; supports `--content <str>`, `--tags <str>`, `--type <str>`, `--project <str>`, `--overwrite`.
   - Probing `bm tool edit-note --help`: Requires `identifier <str>`, `--operation <str>` (`append`, `prepend`, `find_replace`, `replace_section`), and `--content <str>`.
   - Probing `bm tool read-note --help`: Accepts `identifier <str>`, with options `--frontmatter`, `--json`, `--project <str>`.
   - Probing `bm tool search-notes --help`: Discovered hybrid retrieval constraint: executing `bm tool search-notes "*"` failed verbatim with:
     ```
     # Search Failed
     Error searching for '*': Hybrid retrieval requires a non-empty text query and does not support title/permalink-only searches.
     ```
     Executing with `--type task --json` successfully returned structured JSON with active task notes (`Daily Token Spend Optimisation`, `TASK-020 Basic Memory OpenClaw Integration Repair`).
   - Probing `bm orphans --json`: Returned a JSON list of orphan entities:
     ```json
     [{"external_id": "...", "title": "...", "note_type": "...", "file_path": "..."}]
     ```
   - Probing `bm doctor`: Executed successfully, outputting lines prefixed with `OK ...` and concluding verbatim with `Doctor checks passed.`.
   - Probing `bm tool schema-validate`: Outputted JSON dictionary containing `total_notes: 2`, `valid_count: 2`, `warning_count: 1`, `error_count: 0`, and per-note `field_results` and warnings.
   - Probing `bm tool schema-diff Task`: Returned JSON dictionary containing `new_fields` (`cadence`, `constraint`, `follows`, `governed_by`, `supports`) and `dropped_fields` (`steps`, `context`, `started`, `completed`, `blockers`).

3. **Current Codebase State**:
   - Existing codebase at `/Users/kancil/.bmh` currently has 60 unit tests in `tests/`, all passing with 98% coverage (`uv run pytest` completed in 0.49s).
   - Currently, `src/bmh/workflows/` does not exist.
   - `src/bmh/core/client.py` only implements `search_notes(...)`.
   - `src/bmh/ui/menu.py` hosts a flat 6-item menu (`1: Search`, `2: Tasks`, `3: Project`, `4: Recent`, `5: Update`, `0: Exit`).
   - `src/bmh/ui/cards.py` contains `_highlight_observations(...)`, but it is currently not integrated into `render_note_card(...)`.

---

## 2. Logic Chain

1. From Observation 1 & 2, the `bm` CLI is functional, accessible, and provides exact CLI flags and structured JSON outputs matching the requirements in `ORIGINAL_REQUEST.md`.
2. From Observation 2, `bm tool search-notes` enforces strict query rules (hybrid retrieval requires non-empty query or metadata filters, and rejects bare `*`). Therefore, the query builder in `query.py` and `BMClient.search_notes` must ensure valid arguments (passing `--type`, `--status`, or non-wildcard queries) to prevent exit code 1 errors.
3. From Observation 2, the exact JSON shapes for `schema-validate`, `schema-diff`, `orphans`, and `doctor` were extracted directly from live execution, allowing exact Pydantic/dataclass models and Rich UI table layouts to be defined.
4. From Observation 3, implementing R1–R5 requires:
   - Expanding `src/bmh/core/client.py` with 7 new methods (`write_note`, `edit_note`, `read_note`, `schema_validate`, `schema_diff`, `doctor`, `orphans`).
   - Wiring badge and checkbox highlighting into `src/bmh/ui/cards.py`.
   - Creating `src/bmh/workflows/ingest.py` for note capture wizards (5 templates), observation appender, and piped capture.
   - Creating `src/bmh/workflows/query.py` for search, active task inspection with step checkoff, project explorer, recent activity, and Guided Query Co-Pilot.
   - Creating `src/bmh/workflows/lint.py` for schema validation, orphan inspection, sync doctor, schema drift, and unified 'Lint All' dashboard.
   - Refactoring `src/bmh/ui/menu.py` to route the top-level Tri-Modal menu (`1: Ingest`, `2: Query`, `3: Lint`, `4: Update`, `0: Exit`).

---

## 3. Caveats

- **No Caveats**: The host `bm` binary is available, live commands were probed directly, outputs and schemas were captured verbatim, and all 12 acceptance criteria have been fully mapped to verifiable tests and specifications.

---

## 4. Conclusion

The specification mining phase is complete. The exhaustive specification report has been compiled and written to:
`/Users/kancil/.bmh/.agents/survey_spec_miner_1/report.md`

It contains:
- Complete breakdown of R1, R2, R3, R4, R5 and 12 Acceptance Criteria.
- 37 itemized features in the Feature Inventory table.
- 22 detailed edge cases with observed and prescribed behaviors.
- Complete YAML frontmatter and markdown specifications for all 5 Ingest templates (`Task`, `Insight`, `Meeting`, `Decision`, `Scratchpad`).
- Full signatures and contracts for `BMClient` subprocess primitives.
- Exact scoring algorithm and grading rubric for the 'Lint All' health dashboard.
- Comprehensive test strategy and verification commands.

---

## 5. Verification Method

To independently verify these findings:
1. View the specification report:
   `cat /Users/kancil/.bmh/.agents/survey_spec_miner_1/report.md`
2. Verify live `bm` command behaviors on the host:
   `/Users/kancil/.local/bin/bm tool list-projects`
   `/Users/kancil/.local/bin/bm tool schema-validate`
   `/Users/kancil/.local/bin/bm tool schema-diff Task`
   `/Users/kancil/.local/bin/bm orphans --json`
   `/Users/kancil/.local/bin/bm doctor`
3. Run baseline unit test suite in `/Users/kancil/.bmh`:
   `uv run pytest`
