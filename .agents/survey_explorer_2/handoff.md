# Handoff Report: `bm` CLI Environment and Command Specifications

**Agent:** Survey Explorer 2  
**Working Directory:** `/Users/kancil/.bmh/.agents/survey_explorer_2`  
**Handoff Type:** Hard (Task complete)  
**Report File:** `/Users/kancil/.bmh/.agents/survey_explorer_2/report.md`  

---

## 1. Observation

1. **Binary Location & Installation:**
   - Command `which bm` returned `/Users/kancil/.local/bin/bm`.
   - File inspection of `/Users/kancil/.local/bin/bm` showed it is a script entry point pointing to `/Users/kancil/.local/share/uv/tools/basic-memory/bin/python`, importing `basic_memory.cli.main.app`.
   - `bm --version` output: `Basic Memory version: 0.23.2`.
   - Package directory: `/Users/kancil/.local/share/uv/tools/basic-memory/lib/python3.12/site-packages/basic_memory`.

2. **Project Registry State:**
   - `bm tool list-projects` returned JSON identifying active projects: `kancil` (default: true, path `/Users/kancil/kancil`), `kensho` (default: false, path `/Users/kancil/kensho`), `main`, `getting-started`, `doctor-1e3b566b`, `openclaw-kancil-node`.

3. **Subcommand Signatures & Implementation in Source Code:**
   - `basic_memory/cli/commands/tool.py`:
     - Line 584: `write_note(title, folder, content=None, tags=None, note_type="note", project=None, project_id=None, overwrite=False, local=False, cloud=False)`. Reads from stdin if `content is None` and not a TTY (lines 647-648). If `result.get("error")` (line 683), prints error to stderr and exits with `typer.Exit(1)`.
     - Line 700: `read_note(identifier, include_frontmatter=False, json_output=False, plain=False, project=None, ...)`. If note does not exist, exits with code 0 and returns `{"title": null, "permalink": null, "file_path": null, "content": null, "frontmatter": null}`.
     - Line 857: `edit_note(identifier, operation, content, find_text=None, section=None, expected_replacements=1, replace_subsections=True, project=None, ...)`. If error occurs, exits with `typer.Exit(1)` (line 933).
     - Line 1033: `recent_activity(page=1, page_size=10, json_output=False, plain=False, project=None, ...)`.
     - Line 1120: `search_notes(query=None, ... json_output=False, plain=False, ...)`. Exits code 1 with `# No Search Criteria` if query and all filters are missing.
     - Line 1385: `schema_validate(target=None, project=None, ...)`. Always outputs JSON via `_print_json(result)`.
     - Line 1519: `schema_diff(note_type, project=None, ...)`. Always outputs JSON via `_print_json(result)`.
   - `basic_memory/cli/commands/doctor.py`:
     - Line 228: `doctor(local=False, cloud=False)`. Runs local consistency checks in ephemeral project. Output is Rich text only (no `--json` option). Exit code 0 on pass, 1 on fail.
   - `basic_memory/cli/commands/orphans.py`:
     - Line 32: `orphans(project=None, json_output=False, local=False, cloud=False)`. Rich table by default; returns pure JSON array of `[{"external_id", "title", "note_type", "file_path"}]` when `--json` is specified. Exit code 1 on error (e.g. invalid project).

4. **Live Command Runs:**
   - `bm doctor`: Exited with code 0:
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
   - `bm orphans --json`: Exited with code 0, returned 112 unlinked entity objects.
   - `bm tool schema-validate`: Exited with code 0, returned JSON payload with `total_notes: 2`, `valid_count: 2`, `warning_count: 1`, `error_count: 0`.
   - `bm tool schema-diff Task`: Exited with code 0, returned JSON drift analysis with `new_fields`, `dropped_fields`, `cardinality_changes`.
   - `bm tool schema-diff nonexistent`: Exited with code 0, returned `{"error": "No schema found for type 'nonexistent'"}`.
   - `bm tool search-notes --type task --json`: Exited with code 0, returned 2 tasks with observation/step markdown bodies.

5. **Existing `bmh` Codebase State (`/Users/kancil/.bmh`):**
   - `src/bmh/core/client.py` has `BMClient` with only `search_notes`. `execute(args, timeout)` lacks an `input: Optional[str] = None` argument for stdin streaming.
   - `src/bmh/core/models.py` has `NoteModel` and `SearchResult`. Line 71 uses `note_type = item.get("type") or metadata.get("note_type")` where `item.get("type")` in search-notes is `"entity"` rather than the domain note type.
   - `uv run pytest` runs 60 tests and passes 100% in 0.42s.

---

## 2. Logic Chain

1. **Availability & Invocation Path:**
   - Observation 1 establishes that `bm` is located in `/Users/kancil/.local/bin/bm`, which is in the standard user PATH. `BMClient`'s default `shutil.which("bm")` and `BM_PATH` env var resolution will discover this binary successfully.
2. **Subprocess Primitive Coverage Requirements (R5):**
   - Observation 3 & 5 demonstrate that `BMClient` currently only wraps `search-notes`. R5 requires wrapping `search-notes`, `write-note`, `edit-note`, `schema-validate`, `schema-diff`, `doctor`, and `orphans`.
   - Observation 3 shows `write-note` reads from `sys.stdin` when `--content` is not passed. `BMClient.execute` must accept `input: Optional[str] = None` to forward to `subprocess.run(..., input=input)`.
3. **Error Handling Architecture:**
   - Observations 3 & 4 reveal an asymmetry:
     - `write-note`, `edit-note`, `orphans`, and `doctor` exit with non-zero exit codes (code 1) on error.
     - `read-note` exits with code 0 when a note is missing and returns all `null` attributes.
     - `schema-validate` and `schema-diff` exit with code 0 on invalid types and return a dictionary with an `"error"` key.
   - Therefore, `BMClient` cannot rely strictly on `returncode == 0` as proof of operation success; it must inspect JSON payloads for `{"error": ...}` and `null` identities.
4. **Hub Workflows (R2, R3, R4):**
   - Observations 2 & 4 confirm active projects `kancil` and `kensho` exist and can be queried via `bm tool search-notes --project <project>`.
   - Ingest Hub (R2) can implement the 5 note capture templates via `bm tool write-note --title ... --folder ... --type ...` and quick observation appending via `bm tool edit-note <identifier> --operation append --content "- [<cat>] ..."`.
   - Query Hub (R3) can browse active tasks using `bm tool search-notes --type task --json` and toggle task steps with `bm tool edit-note <identifier> --operation find_replace --find-text "1. [ ] <step>" --content "1. [x] <step>"`.
   - Lint Hub (R4) can execute all 4 diagnostics using `bm tool schema-validate`, `bm orphans --json`, `bm doctor`, and `bm tool schema-diff <type>`.

---

## 3. Caveats

- **No write operations performed on live projects:** To preserve workspace integrity, no disruptive `write-note` or `edit-note` modifications were executed against live notes in `/Users/kancil/kancil` or `/Users/kancil/kensho`. The exact behavior and JSON structures for write/edit operations were verified through full python source code inspection of the installed `basic_memory` 0.23.2 package and test suite.
- **Doctor Project Generation:** Running `bm doctor` temporarily creates and tears down a doctor project (e.g. `doctor-b8b4f0de`). It runs purely local consistency checks and does not touch user notes.

---

## 4. Conclusion

The `bm` CLI environment is fully functional, up-to-date (`0.23.2`), and exposes all necessary primitives for the Tri-Modal CLI architecture. All commands required by the specification (`search-notes`, `write-note`, `edit-note`, `schema-validate`, `schema-diff`, `doctor`, `orphans`, `list-projects`, `recent-activity`, `read-note`) have verified signatures, documented argument requirements, and mapped JSON/text outputs.

Comprehensive findings, JSON schemas, edge case analyses, and implementation blueprints have been compiled into `/Users/kancil/.bmh/.agents/survey_explorer_2/report.md`.

---

## 5. Verification Method

To independently verify the findings in this report:

1. **Verify Binary & Version:**
   ```bash
   which bm
   bm --version
   ```
   *Expected:* `/Users/kancil/.local/bin/bm` and `Basic Memory version: 0.23.2`.

2. **Verify Project Discovery:**
   ```bash
   bm tool list-projects
   ```
   *Expected:* Valid JSON array showing `kancil` as default project and `kensho` as secondary project.

3. **Verify Diagnostic Commands (Lint Hub):**
   ```bash
   bm doctor
   bm orphans --json
   bm tool schema-validate
   bm tool schema-diff Task
   ```
   *Expected:* `Doctor checks passed.`, JSON array of orphans, schema validation report JSON, and schema diff JSON.

4. **Verify Query Commands (Query Hub):**
   ```bash
   bm tool search-notes --type task --json
   bm tool read-note "tasks/daily-token-spend-optimisation.md" --json
   bm tool recent-activity --json
   ```
   *Expected:* Structured JSON envelopes with task notes and recent activity.

5. **Verify Unit Tests in Repo:**
   ```bash
   cd /Users/kancil/.bmh && uv run pytest
   ```
   *Expected:* 60 passing tests.
