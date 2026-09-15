# AGENTS.md - AI Agent Context & Developer Handbook for `bmh`

This document bootstraps any AI coding assistant (Antigravity, Claude, Codex, Gemini, Cursor, etc.) working on `bmh`. Read this before modifying the codebase.

---

## 1. Project Mission & Identity

- **Name**: `bmh` (Basic Memory Helper)
- **Role**: A purely interactive CLI companion and structured card inspector for **Basic Memory** (`bm`).
- **Core Philosophy**:
  1. **Fix Inputs**: Guide the user step-by-step through interactive user stories. Users should NEVER need to memorize verbose CLI flags.
  2. **Fix Outputs**: Present notes as clean, structured **Cards** (Header: title/index, Body: markdown/observations/steps, Footer: entity/external_id) without context pollution.
  3. **Zero-Pollution**: Keep outputs dense, high-signal, and formatted.

---

## 2. Git & Branching Rules (Strict)

- **`main`**: Production / Stable releases only. Installed on user machines. **NEVER commit directly to `main`**.
- **`develop`**: Integration branch for ongoing work.
- **`feature/<name>`**: Individual user stories or features. Branch off `develop`, merge back into `develop`, and create release tags when merging into `main`.

---

## 3. Commit Convention (Commitizen / Conventional Commits)

All commits MUST adhere to Conventional Commits:
`<type>(<scope>): <short description>`

### Allowed Types:
- `feat`: New feature or user story (e.g. `feat(search): add tag-based filtering wizard`)
- `fix`: Bug fix (e.g. `fix(ui): resolve symlink path resolution on macOS`)
- `docs`: Documentation updates (`docs(readme): document update command`)
- `refactor`: Code restructuring without functional changes
- `test`: Adding or modifying tests
- `chore`: Maintenance, version bumps, or build changes

---

## 4. Architecture & Directory Layout

```text
~/.bmh/
├── AGENTS.md            # This agent onboarding guide
├── CONTRIBUTING.md      # Developer guidelines & contribution flow
├── .cz.json             # Commitizen configuration
├── Makefile             # 'make install', 'make test', 'make dev'
├── pyproject.toml       # Python project configuration (hatchling build-backend)
├── src/
│   └── bmh/
│       ├── __init__.py
│       ├── main.py              # Pure interactive entrypoint + Stdin pipe + update
│       ├── core/
│       │   ├── __init__.py
│       │   ├── client.py        # bm CLI subprocess client & path discovery
│       │   └── models.py        # Pydantic Note, Task, SearchResult schemas & normalizers
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── banner.py        # Rich ASCII / box header banners
│       │   ├── cards.py         # Rich Panel card renderer with Markdown & badges
│       │   └── menu.py          # Interactive prompt flows (search, tasks, projects, recent)
│       └── updater/
│           ├── __init__.py
│           └── engine.py        # Multi-environment updater (uv tool, pipx, git)
└── tests/
    ├── test_banner.py
    ├── test_cards.py
    ├── test_client.py
    ├── test_main.py
    ├── test_menu.py
    ├── test_models.py
    └── test_updater.py
```

---

## 5. UI & Card Formatting Invariants

When rendering notes in `bmh.ui.cards`:
- Cards MUST contain:
  1. **Header**: `📌 Note Title [Index/Total]`
  2. **Body**: Formatted Markdown content with highlighted badges (`[decision]`, `[insight]`, `[risk]`, `[todo]`, `[status]`) and checkboxes (`☑`, `☐`)
  3. **Footer/Subtitle**: `entity: <permalink>` and `external_id: <uuid>`
- Handle raw JSON arrays, wrapper objects (`.results`, `.items`), and single objects cleanly using `normalize_notes_json`.

---

## 6. How to Test & Verify

Before submitting changes:
```bash
# 1. Run unit test suite with coverage
make test

# 2. Test interactive launch locally
uv run bmh --help
uv run bmh -v

# 3. Test piped execution with real bm notes
bm tool search-notes --type task --json | uv run bmh
```

---

## 7. Version Bumping & Releases

When releasing a new version:
1. Update `version = "x.y.z"` in `pyproject.toml` and `__version__` in `src/bmh/__init__.py`.
2. Update version references in documentation.
3. Merge `develop` into `main`.
4. Create an annotated git tag: `git tag -a vx.y.z -m "Release vx.y.z"`.
5. Push to GitHub: `git push origin main --tags`.
