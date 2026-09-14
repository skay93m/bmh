# AGENTS.md - AI Agent Context & Developer Handbook for `bmh`

This document bootstraps any AI coding assistant (Antigravity, Claude, Codex, Gemini, Cursor, etc.) working on `bmh`. Read this before modifying the codebase.

---

## 1. Project Mission & Identity

- **Name**: `bmh` (Basic Memory Helper)
- **Role**: A purely interactive CLI companion for **Basic Memory** (`bm`).
- **Core Philosophy**:
  1. **Fix Inputs**: Guide the user step-by-step through interactive user stories. Users should NEVER need to memorize verbose CLI flags.
  2. **Fix Outputs**: Present notes as clean, structured **Cards** (Header: title/index, Body: markdown/observations/steps, Footer: ID/entity/file/timestamp) without context pollution.
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
├── Makefile             # 'make install', 'make test', 'make commit'
├── install.sh           # Symlinker to ~/.local/bin/bmh
├── bin/
│   └── bmh              # Main executable entrypoint (100% interactive walkthrough)
└── lib/
    ├── ui.sh            # Terminal styling, banners, and Card renderer (jq)
    └── bm.sh            # Basic Memory wrapper utilities (future expansion)
```

---

## 5. UI & Card Formatting Invariants

When rendering notes in `lib/ui.sh`:
- Cards MUST contain:
  1. **Header**: `📌 [Index/Total] Note Title`
  2. **Separator**: ASCII or Box-drawing line (`───`)
  3. **Body**: Markdown content / observations / steps
  4. **Separator**: ASCII or Box-drawing line (`───`)
  5. **Footer**: External ID, Entity permalink, Type, File path, formatted Timestamp (`DD/MM/YY HH:MM`)
- Handle raw JSON arrays, wrapper objects (`.results`), and single objects cleanly using `to_rows` normalization in `jq`.

---

## 6. How to Test & Verify

Before submitting changes:
```bash
# 1. Run syntax verification
make test

# 2. Test interactive launch locally
bin/bmh --help
bin/bmh -v

# 3. Test piped execution with real bm notes
bm tool search-notes --type task --json | bin/bmh
```

---

## 7. Version Bumping & Releases

When releasing a new version:
1. Update `VERSION="x.y.z"` in `bin/bmh`.
2. Update version references in documentation.
3. Merge `develop` into `main`.
4. Create an annotated git tag: `git tag -a vx.y.z -m "Release vx.y.z"`.
5. Push to GitHub: `git push origin main --tags`.
