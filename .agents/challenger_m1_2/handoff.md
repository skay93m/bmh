# Empirical Challenge Report: UI Cards Rendering & Observation Highlighting Stress

**Milestone**: M1 (Subprocess Execution & UI Primitives Foundation)  
**Target File**: `src/bmh/ui/cards.py`  
**Challenger**: Challenger M1-2 (`.agents/challenger_m1_2`)  
**Verdict**: `REQUEST_CHANGES`  
**Date**: 2026-09-16  

---

## 1. Observation

Direct empirical stress testing was executed against all functions and classes in `src/bmh/ui/cards.py` across 7 test batteries (highlighting, note cards, schema validation, orphan links, doctor consistency, schema drift, and unified lint dashboard). The following unhandled exceptions and rendering crashes were observed:

### Observation 1.1: `MarkupError` Crash in `render_note_card` (Title & Subtitle)
- **File**: `src/bmh/ui/cards.py`, lines 63–64, 80–98:
  ```python
  63:     counter_str = f" [{index}/{total}]" if total > 1 else ""
  64:     header_title = f"📌 {note.title}{counter_str}"
  ...
  82:     if note.entity:
  83:         footer_elements.append(f"[bold cyan]entity:[/bold cyan] {note.entity}")
  ...
  94:     return Panel(
  95:         body_renderable,
  96:         title=header_title,
  ...
  98:         subtitle=subtitle,
  ```
- **Reproduction Command**:
  ```bash
  uv run python3 -c "
  from rich.console import Console
  from bmh.ui.cards import render_note_card
  from bmh.core.models import NoteModel

  c = Console()
  note = NoteModel(title='[/red]', content='hello')
  c.print(render_note_card(note))
  "
  ```
- **Verbatim Error**:
  ```text
  rich.errors.MarkupError: closing tag '[/red]' at position 2 doesn't match any open tag
  ```
- **Impact**: Any note whose title or metadata (`entity`, `external_id`, `file_path`, `updated_at`) contains closing brackets or mismatched markup tags (e.g. `[/red]`, `[/]`, `[bold][/dim]`, `notes/[/archive]/file.md`) crashes the entire CLI process with an uncaught `MarkupError`.

### Observation 1.2: Instant `MarkupError` Crash in `render_doctor_panel`
- **File**: `src/bmh/ui/cards.py`, lines 281–286:
  ```python
  281:         elements.append(
  282:             Text.from_markup(
  283:                 f"[bold red]🩺 Doctor Status: Check Failed[/bold red]\n"
  284:                 f"[dim]{output or 'Consistency check failed'}[/dim]"
  285:             )
  286:         )
  ```
- **Reproduction Command**:
  ```bash
  uv run python3 -c "
  from bmh.ui.cards import render_doctor_panel
  data = {'passed': False, 'output': 'Error in index [0]: missing [/key]'}
  panel = render_doctor_panel(data)
  "
  ```
- **Verbatim Error**:
  ```text
  Traceback (most recent call last):
    File "<string>", line 4, in <module>
      panel = render_doctor_panel(data)
    File ".../bmh/ui/cards.py", line 282, in render_doctor_panel
      Text.from_markup(
      ...
    File ".../rich/markup.py", line 167, in render
      raise MarkupError(
          f"closing tag '{tag.markup}' at position {position} doesn't match any open tag"
      ) from None
  rich.errors.MarkupError: closing tag '[/key]' at position 84 doesn't match any open tag
  ```
- **Impact**: Unlike other renderers which crash during console drawing, `render_doctor_panel` crashes during panel *creation* whenever `bm doctor` output contains bracketed strings (such as error paths, indices, or tags).

### Observation 1.3: Instant `MarkupError` Crash in `render_schema_diff_panel`
- **File**: `src/bmh/ui/cards.py`, lines 319–320:
  ```python
  319:         return Panel(
  320:             Text.from_markup(f"[bold yellow]No schema definition found for note type '{note_type}'.[/bold yellow]"),
  ...
  362:             table_new.add_row(
  363:                 str(f.get("name", "")),
  ...
  384:             table_drop.add_row(
  385:                 str(f.get("name", "")),
  ```
- **Reproduction Command**:
  ```bash
  uv run python3 -c "
  from bmh.ui.cards import render_schema_diff_panel
  panel = render_schema_diff_panel({'schema_found': False, 'note_type': '[/custom]'})
  "
  ```
- **Verbatim Error**:
  ```text
  rich.errors.MarkupError: closing tag '[/custom]' at position 55 doesn't match any open tag
  ```
- **Impact**: Any custom note type or field name containing brackets crashes with `MarkupError`.

### Observation 1.4: `MarkupError` in `render_schema_validation_panel` and `render_orphan_list_panel`
- **File**: `src/bmh/ui/cards.py`, line 179 and line 230:
  ```python
  179:             table.add_row(ident, schema, status, issues)
  ...
  230:         table.add_row(
  231:             str(idx),
  232:             str(item.get("title", "Untitled")),
  ...
  ```
- **Reproduction Command**:
  ```bash
  uv run python3 -c "
  from rich.console import Console
  from bmh.ui.cards import render_schema_validation_panel, render_orphan_list_panel

  c = Console()
  p1 = render_schema_validation_panel({
      'total_notes': 1, 'results': [{'note_identifier': 'N1', 'errors': ['Syntax error in tag [/tag]']}]
  })
  c.print(p1)
  "
  ```
- **Verbatim Error**:
  ```text
  rich.errors.MarkupError: closing tag '[/tag]' at position 20 doesn't match any open tag
  ```
- **Impact**: Validation errors reporting tag mismatches or syntax issues crash the terminal when rendered.

### Observation 1.5: `TypeError` Crash in `render_lint_all_dashboard` on Null Schema Counts
- **File**: `src/bmh/ui/cards.py`, lines 416, 430, 467:
  ```python
  416:     total_notes = schema_data.get("total_notes", results.get("total_notes", 0))
  ...
  430:         schema_ratio = (valid_count / max(total_notes, 1)) if total_notes > 0 else 1.0
  ...
  467:     schema_status = "[bold red]FAIL[/bold red]" if errors > 0 else ...
  ```
- **Reproduction Command**:
  ```bash
  uv run python3 -c "
  from bmh.ui.cards import render_lint_all_dashboard
  results = {'schema': {'total_notes': None, 'valid_count': None, 'warning_count': None, 'error_count': None}}
  render_lint_all_dashboard(results)
  "
  ```
- **Verbatim Error**:
  ```text
  Traceback (most recent call last):
    File "<string>", line 4, in <module>
      render_lint_all_dashboard(results)
    File ".../bmh/ui/cards.py", line 430, in render_lint_all_dashboard
      schema_ratio = (valid_count / max(total_notes, 1)) if total_notes > 0 else 1.0
                                                            ^^^^^^^^^^^^^^^^
  TypeError: '>' not supported between instances of 'NoneType' and 'int'
  ```
- **Impact**: When deserialized payloads contain nullable schema count fields (`total_notes: None`), `.get("total_notes", 0)` returns `None` instead of `0`, crashing with `TypeError`.

### Observation 1.6: `TypeError` Crash on String/Non-Int Scores in `render_lint_all_dashboard`
- **File**: `src/bmh/ui/cards.py`, line 439:
  ```python
  439:         if score >= 90:
  ```
- **Reproduction Command**:
  ```bash
  uv run python3 -c "
  from bmh.ui.cards import render_lint_all_dashboard
  render_lint_all_dashboard({'health_score': '100'})
  "
  ```
- **Verbatim Error**:
  ```text
  TypeError: '>=' not supported between instances of 'str' and 'int'
  ```

### Observation 1.7: `AttributeError` on Non-Dict Items in Lists
- **File**: `src/bmh/ui/cards.py`, line 232 (`render_orphan_list_panel`) and lines 358, 380 (`render_schema_diff_panel`):
  ```python
  232:             str(item.get("title", "Untitled")),
  ...
  358:             table_new.add_row(str(f.get("name", "")), ...)
  ```
- **Reproduction Command**:
  ```bash
  uv run python3 -c "
  from bmh.ui.cards import render_orphan_list_panel
  render_orphan_list_panel([None])
  "
  ```
- **Verbatim Error**:
  ```text
  AttributeError: 'NoneType' object has no attribute 'get'
  ```

### Observation 1.8: `TypeError` on `None` in `highlight_observations`
- **File**: `src/bmh/ui/cards.py`, lines 29–34:
  ```python
  def highlight_observations(content: str) -> str:
      highlighted = content
      for pattern, replacement in TAG_REPLACEMENTS.items():
          highlighted = pattern.sub(replacement, highlighted)
      return highlighted
  ```
- **Reproduction Command**:
  ```bash
  uv run python3 -c "
  from bmh.ui.cards import highlight_observations
  highlight_observations(None)
  "
  ```
- **Verbatim Error**:
  ```text
  TypeError: expected string or bytes-like object, got 'NoneType'
  ```

### Observation 1.9: Observation Badges Modifying Code Blocks & Code Fences
- **File**: `src/bmh/ui/cards.py`, lines 29–34:
  - Input: `` `[decision]` in code ``
  - Output: `` `[bold green]\[decision][/bold green]` in code ``
- **Impact**: Replacing tags inside backticks or fenced blocks injects raw Rich markup into code snippets.

---

## 2. Logic Chain

1. **Requirement Check**:
   - `DISPATCH.md` instructs: "Verify renderers never crash Rich or throw unhandled exceptions."
   - `ORIGINAL_REQUEST.md` R5 & Acceptance Criteria requires: "Subprocess errors and missing bm binaries are handled gracefully without uncaught tracebacks."
2. **Analysis of Current Implementation**:
   - Rich console by default interprets raw strings in `Panel(title=str)`, `Panel(subtitle=str)`, `Table.add_row(*strs)`, and `Text.from_markup(str)` as Rich Console Markup tags.
   - Observations 1.1, 1.2, 1.3, 1.4 prove that when user note data, doctor error output, schema drift fields, or validation error messages contain bracketed syntax (e.g. `[/tag]`, `[/error]`, `[/0]`), Rich's markup parser fails and raises `rich.errors.MarkupError`.
   - Because `render_note_card` only catches markup errors in `note.content` (lines 71–78) but passes `note.title` and `subtitle` directly into `Panel()`, the title and metadata remain completely unshielded.
   - In `render_doctor_panel`, line 282 calls `Text.from_markup(...)` directly on the unescaped CLI stdout `output`. Any error output containing brackets throws `MarkupError` immediately upon panel instantiation.
   - In `render_lint_all_dashboard`, dictionary lookups `.get(key, 0)` do not protect against keys whose value is explicitly `None` (e.g. `{"total_notes": None}`). When evaluated against `> 0`, Python raises `TypeError`.
   - In `render_orphan_list_panel` and `render_schema_diff_panel`, list elements are assumed to always be dicts/BaseModels without checking `if isinstance(item, dict)`.
   - In `highlight_observations`, `content` is not guarded against `None`.
3. **Conclusion Inference**:
   - The UI card renderers violate the core stability requirement: they crash Rich and raise unhandled exceptions on realistic inputs.
   - Therefore, Milestone M1 UI components cannot be approved without remediating these unhandled exceptions.

---

## 3. Caveats

- Milestone M1 implementation is otherwise well-structured with high initial test coverage (28 passing tests in `tests/test_cards.py`) and fast performance under large text volumes (154,000 characters processed in 4.3ms).
- Rendering with clean, valid data (happy path) functions as expected.
- No caveats regarding reproducibility: every crash listed in Section 1 was reproduced with standalone commands and verified on Python 3.14.7.

---

## 4. Conclusion

**Verdict: `REQUEST_CHANGES`**

The implementation in `src/bmh/ui/cards.py` must be updated to address the following required fixes:

1. **Protect Panel Titles and Subtitles from `MarkupError`**:
   - In `render_note_card`: Use `Text(header_title)` instead of a raw formatted string, or escape user fields using `from rich.markup import escape`. Build `subtitle` safely using `Text` / `Text.assemble` or `escape(...)`.
2. **Protect Diagnostic Panels from `MarkupError`**:
   - In `render_doctor_panel`: Avoid `Text.from_markup` on raw `output`. Use `Text.assemble(("🩺 Doctor Status: Check Failed\n", "bold red"), (output or "Consistency check failed", "dim"))` or `escape(output)`.
   - In `render_schema_diff_panel`: Escape `note_type` in line 320 or use `Text.assemble`. Wrap field names and sources in `Text(...)` or `escape(...)` before passing to `table.add_row(...)`.
   - In `render_schema_validation_panel` and `render_orphan_list_panel`: Wrap table cell strings in `Text(...)` or `escape(...)` so bracketed identifiers, error messages, and file paths cannot trigger `MarkupError`.
3. **Null-Safe and Type-Safe Numeric Aggregation in `render_lint_all_dashboard`**:
   - Coerce numeric fields using a helper like:
     ```python
     def _int(val: Any, default: int = 0) -> int:
         try:
             return int(val) if val is not None else default
         except (ValueError, TypeError):
             return default
     ```
   - Convert `health_score` to `int` safely before performing comparisons (`if score >= 90`).
4. **List Item Type Guard**:
   - In `render_orphan_list_panel` and `render_schema_diff_panel`, ensure `if not isinstance(item, dict): continue` or guard against `None`.
5. **Guard `highlight_observations`**:
   - Add `if not content: return "" if content is not None else ""` at the start of `highlight_observations`.

---

## 5. Verification Method

To independently verify these findings, run the following stress harness:

```bash
uv run python3 - << 'EOF'
from rich.console import Console
from bmh.ui.cards import (
    highlight_observations,
    render_note_card,
    render_schema_validation_panel,
    render_orphan_list_panel,
    render_doctor_panel,
    render_schema_diff_panel,
    render_lint_all_dashboard,
)
from bmh.core.models import NoteModel

c = Console()

# 1. highlight_observations None crash
try:
    highlight_observations(None)
except TypeError as e:
    print(f"[REPRODUCED] highlight_observations(None): {e}")

# 2. render_note_card MarkupError
try:
    note = NoteModel(title="[/red]", content="content")
    c.print(render_note_card(note))
except Exception as e:
    print(f"[REPRODUCED] render_note_card MarkupError: {e}")

# 3. render_doctor_panel MarkupError
try:
    render_doctor_panel({"passed": False, "output": "Failed [/key]"})
except Exception as e:
    print(f"[REPRODUCED] render_doctor_panel MarkupError: {e}")

# 4. render_schema_diff_panel MarkupError
try:
    render_schema_diff_panel({"schema_found": False, "note_type": "[/custom]"})
except Exception as e:
    print(f"[REPRODUCED] render_schema_diff_panel MarkupError: {e}")

# 5. render_lint_all_dashboard TypeError
try:
    render_lint_all_dashboard({"schema": {"total_notes": None}})
except Exception as e:
    print(f"[REPRODUCED] render_lint_all_dashboard TypeError: {e}")
EOF
```

Expected output: All 5 reproductions trigger their respective `TypeError` or `MarkupError` exceptions, confirming the vulnerabilities.
