## Worker M1 Dispatch: Subprocess Execution & UI Primitives Foundation
You are Worker M1 for the bmh Tri-Modal CLI project.
Your working directory is `/Users/kancil/.bmh/.agents/worker_m1`.

You MUST read:
- `/Users/kancil/.bmh/.agents/ORIGINAL_REQUEST.md` (authoritative user requirements)
- `/Users/kancil/.bmh/PROJECT.md` (architecture, interface contracts, feature inventory)
- `/Users/kancil/.bmh/.agents/survey_explorer_1/report.md` (codebase layout & gap analysis)
- `/Users/kancil/.bmh/.agents/survey_explorer_2/report.md` (exact CLI command signatures, arguments, outputs)
- `/Users/kancil/.bmh/.agents/survey_spec_miner_1/report.md` (schemas, models, badges)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Exclusive Write Ownership:
- `src/bmh/core/client.py`
- `src/bmh/core/models.py`
- `src/bmh/ui/cards.py`
- `tests/test_client.py`
- `tests/test_cards.py`
DO NOT touch other files.

Requirements for Milestone M1:
1. In `src/bmh/core/client.py`:
   - Expand `BMClient.execute` to accept `input: Optional[str] = None` for stdin streaming.
   - Implement typed, robust methods for all 7+ `bm` primitives:
     - `search_notes(query, project, note_type, status, is_title, json_output)`
     - `write_note(title, folder, content, tags, note_type, project, overwrite, input_content)`
     - `edit_note(identifier, operation, content, find_text, section, expected_replacements, project)`
     - `read_note(identifier, project)` (handle exit 0 with null fields)
     - `schema_validate(target, project)` (handle exit 0 with {"error": ...})
     - `schema_diff(note_type, project)` (handle exit 0 with {"error": ...})
     - `doctor()` (parse text output for status, steps, passed)
     - `orphans(project)` (handle JSON array)
     - `recent_activity(page, page_size, project)`
     - `list_projects()`
   - Graceful error shielding: No uncaught tracebacks; return informative dict/exception details.
2. In `src/bmh/core/models.py`:
   - Enhance models as needed for lint diagnostics, task items, templates, and note content.
3. In `src/bmh/ui/cards.py`:
   - Ensure `_highlight_observations` is applied inside `render_note_card` so `[decision]`, `[risk]`, `[insight]`, `[todo]`, `[status]`, `[x]`, `[ ]` are styled with Rich text/badges.
   - Implement diagnostic renderers: `render_schema_validation_panel`, `render_orphan_list_panel`, `render_doctor_panel`, `render_schema_diff_panel`, `render_lint_all_dashboard`.
4. Update `tests/test_client.py` and `tests/test_cards.py` to cover all new methods, edge cases, and panel renderers.
5. Verify build and tests pass via `uv run pytest tests/test_client.py tests/test_cards.py`.
6. Write full completion report to `handoff.md` in your working directory.

## 2026-09-16T00:26:30Z
You are Worker M1 for the bmh Tri-Modal CLI project.
Your working directory is /Users/kancil/.bmh/.agents/worker_m1.
Read /Users/kancil/.bmh/.agents/ORIGINAL_REQUEST.md, /Users/kancil/.bmh/PROJECT.md, and your dispatch file at /Users/kancil/.bmh/.agents/worker_m1/DISPATCH.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement Milestone M1 (Subprocess Execution & UI Primitives Foundation):
- Exclusive write ownership: src/bmh/core/client.py, src/bmh/core/models.py, src/bmh/ui/cards.py, tests/test_client.py, tests/test_cards.py.
- Implement 7+ BMClient primitives with stdin streaming, payload inspection, and error shielding.
- Enhance ui/cards.py with observation badge formatting ([decision], [risk], [insight], [todo], [status], [x], [ ]) and diagnostic panels (schema validation, orphans, doctor, schema diff, lint all).
- Update and add comprehensive unit tests in tests/test_client.py and tests/test_cards.py.
- Verify tests pass with uv run pytest tests/test_client.py tests/test_cards.py.
- Write your completion report to /Users/kancil/.bmh/.agents/worker_m1/handoff.md and notify the orchestrator.

