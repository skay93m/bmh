## Worker M1 Iteration 2 Dispatch: Defensive Hardening & Bug Remediation
You are Worker M1 Iteration 2 for the bmh Tri-Modal CLI project.
Your working directory is `/Users/kancil/.bmh/.agents/worker_m1_it2`.

You MUST read:
- `/Users/kancil/.bmh/.agents/ORIGINAL_REQUEST.md`
- `/Users/kancil/.bmh/PROJECT.md`
- `/Users/kancil/.bmh/.agents/orchestrator_1/GATE_STATUS.md`
- `/Users/kancil/.bmh/.agents/challenger_m1_1/handoff.md` (exact reproduction cases for client & model bugs)
- `/Users/kancil/.bmh/.agents/challenger_m1_2/handoff.md` (exact reproduction cases for cards.py crashes)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Exclusive Write Ownership:
- `src/bmh/core/client.py`
- `src/bmh/core/models.py`
- `src/bmh/ui/cards.py`
- `tests/test_client.py`
- `tests/test_cards.py`

Required Remediations:
1. In `src/bmh/ui/cards.py`:
   - Import `from rich.markup import escape`.
   - In `highlight_observations(content)`: if `not content`: return `""`.
   - In `render_note_card`: Escape `note.title`, `counter_str`, and metadata fields (`note.entity`, `note.external_id`, `note.file_path`, `note.updated_at`) using `escape(...)` or pass `Text` to `title` and `subtitle` to prevent `MarkupError` when user content contains tags like `[/red]` or brackets.
   - In `render_doctor_panel`: Avoid `Text.from_markup` on unescaped `output`. Use `escape(output or "Consistency check failed")` or `Text.assemble(...)`.
   - In `render_schema_diff_panel`: Escape `note_type`, field names, and sources. Ensure `table.add_row` receives escaped strings.
   - In `render_schema_validation_panel` and `render_orphan_list_panel`: Escape all table cells (`escape(str(item.get(...)))`).
   - In `render_lint_all_dashboard`:
     - Provide a safe `_int(val, default=0)` helper for `total_notes`, `valid_count`, `warning_count`, `error_count`, and `score`. Guard against `None` values (e.g. `schema.get("total_notes")` returning `None`).
     - Safely convert `health_score` from `results` using `_int(results.get("health_score"))` before doing comparisons like `if score >= 90`.
   - In `render_orphan_list_panel` and `render_schema_diff_panel`: Guard list items (`if not isinstance(item, (dict, BaseModel)): continue`). If passed a dict error payload like `{"error": ...}`, render an error panel instead of crashing.

2. In `src/bmh/core/client.py`:
   - In `BMClient.orphans()`: Catch `json.JSONDecodeError` on empty string or malformed stdout, returning `[]` or raising informative `BMError`.

3. In `src/bmh/core/models.py`:
   - In `normalize_notes_json` and `NoteModel`: Coerce all items in `tags` to `str` (e.g. `tags = [str(t) for t in tags] if tags else []`) so numeric tags like `[2024, 2025]` do not trigger Pydantic validation errors.

4. Tests:
   - Run the reproduction scripts from `challenger_m1_1/handoff.md` and `challenger_m1_2/handoff.md`.
   - Update and add regression unit tests in `tests/test_client.py` and `tests/test_cards.py`.
   - Verify `uv run pytest tests/test_client.py tests/test_cards.py` passes 100%.
   - Verify `uv run pytest tests/test_m1_stress_suite.py` passes all tests without xfails if present.
   - Verify full test suite `uv run pytest`.

5. Write full completion report to `/Users/kancil/.bmh/.agents/worker_m1_it2/handoff.md` and notify orchestrator.

## 2026-09-16T00:35:50Z
You are Worker M1 Iteration 2 for the bmh Tri-Modal CLI project.
Your working directory is /Users/kancil/.bmh/.agents/worker_m1_it2.
Read /Users/kancil/.bmh/.agents/ORIGINAL_REQUEST.md, /Users/kancil/.bmh/PROJECT.md, /Users/kancil/.bmh/.agents/orchestrator_1/GATE_STATUS.md, and your dispatch at /Users/kancil/.bmh/.agents/worker_m1_it2/DISPATCH.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Remediate all issues identified by Challenger M1-1 and Challenger M1-2 in cards.py, client.py, models.py:
1. cards.py: escape markup in titles, subtitles, table rows, doctor output; guard highlight_observations on None; safe _int helper for nullable numeric schema counts and string health_score in render_lint_all_dashboard; type guards for list items.
2. client.py: catch JSONDecodeError in BMClient.orphans on empty/malformed stdout.
3. models.py: coerce tags to str so numeric tags pass validation.
4. Add tests covering all these edge cases in tests/test_client.py and tests/test_cards.py.
5. Verify tests with uv run pytest.
6. Write handoff to /Users/kancil/.bmh/.agents/worker_m1_it2/handoff.md and notify orchestrator.
