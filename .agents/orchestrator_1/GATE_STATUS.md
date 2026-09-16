# Gate Status: bmh Tri-Modal CLI Architecture

## Gate — Milestone M1 (Iteration 1)
| Agent | Role | Verdict | Source | Notes |
|-------|------|---------|--------|-------|
| worker_m1 | teamwork_preview_worker | DONE | handoff.md | 72/72 tests pass, 95% cov |
| reviewer_m1_1 | teamwork_preview_reviewer | APPROVE | handoff.md | Code quality & contracts pass |
| reviewer_m1_2 | teamwork_preview_reviewer | APPROVE | handoff.md | Edge cases & errors pass |
| challenger_m1_1 | teamwork_preview_challenger | REQUEST_CHANGES | handoff.md | 3 issues: orphans JSONDecodeError on empty/malformed stdout, normalize_notes_json tag coercion, orphan list panel error dicts |
| challenger_m1_2 | teamwork_preview_challenger | REQUEST_CHANGES | handoff.md | 11 issues: MarkupError on raw strings with brackets, TypeError on null numeric fields, highlight_observations(None) |
| auditor_m1_1 | teamwork_preview_auditor | CLEAN | handoff.md | Zero mock cheats, non-vacuous tests, authentic implementation |

Gate Result: **FAIL** (challenger_m1_1 & challenger_m1_2 REQUEST_CHANGES)
Remediation required in Iteration 2:
1. `src/bmh/ui/cards.py`:
   - Wrap panel titles, subtitles, table cells, and diagnostic output with `rich.markup.escape()` or `Text()` to prevent `MarkupError` when inputs contain bracketed tokens or closing tags.
   - Guard `highlight_observations(content)` against `None` (return `""`).
   - In `render_lint_all_dashboard`, use safe integer coercion `_int(val)` for nullable schema count fields (`total_notes: None`) and string health scores to prevent `TypeError`.
   - In `render_orphan_list_panel` and `render_schema_diff_panel`, guard list items to ensure `isinstance(item, dict)` or `isinstance(item, BaseModel)`.
2. `src/bmh/core/client.py`:
   - In `BMClient.orphans()`, catch `json.JSONDecodeError` on malformed or empty string stdout, returning `[]` or raising informative `BMError`.
3. `src/bmh/core/models.py`:
   - In `normalize_notes_json` / `NoteModel`, coerce all items in `tags` to `str` (e.g. `[str(t) for t in tags]`) so numeric tags like `[2024, 2025]` do not trigger Pydantic validation errors.
