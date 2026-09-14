# Contributing to bmh

Thank you for contributing to `bmh`!

---

## 1. Branching Strategy (Git Flow)

- `main` is strictly reserved for stable, tagged releases.
- All active development happens on `develop` or topic branches `feature/<name>`.

```bash
# Start a new feature
git checkout develop
git checkout -b feature/my-new-story

# Finish feature
git checkout develop
git merge --no-ff feature/my-new-story
git push origin develop
```

---

## 2. Commit Message Standards (Conventional Commits)

Commit messages must follow the format:
```text
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Examples:
- `feat(search): add date range filter to search flow`
- `fix(card): prevent word wrap overflow in note titles`
- `docs(agents): update testing guidelines for agents`
- `chore(release): bump version to 1.1.0`

You can also run `make commit` for an interactive prompt wizard.

---

## 3. Pre-Commit Checklist

Before opening a PR or merging to `develop`:
1. Run syntax validation: `make test`
2. Test the interactive flow: `bin/bmh`
3. Verify Card output: `bm tool search-notes --type task --json | bin/bmh`
