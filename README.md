# bmh (Basic Memory Helper)

A purely interactive companion and structured card inspector for **Basic Memory** (`bm`), built in Python 3.12+ with `typer`, `rich`, and `pydantic`.

Instead of memorizing flags and parsing unformatted JSON, `bmh` provides a guided walkthrough for searching and exploring your knowledge base, rendering every result in clean, structured cards.

---

## 🚀 Installation

`bmh` is distributed as a standalone Python CLI tool and can be installed via `uv` or `pipx`.

### ⚡ Recommended: `uv tool`

```bash
# Install directly from GitHub
uv tool install git+https://github.com/skay93m/bmh.git --force

# Or install locally in a cloned directory
git clone https://github.com/skay93m/bmh.git ~/.bmh
cd ~/.bmh && uv tool install . --force
```

---

### 📦 Alternative: `pipx`

```bash
pipx install git+https://github.com/skay93m/bmh.git
```

---

## 🔄 Updating to Latest Version

On any machine with `bmh` installed, simply run:
```bash
bmh update
```
*(Or select option `[5]` from the interactive menu).*

`bmh update` automatically detects your environment (`uv tool`, `pipx`, or local `git` repo) and applies the latest release seamlessly.

---

## 📖 Usage

### Interactive Walkthrough (Human Default)
Simply launch `bmh` in your terminal:

```bash
bmh
```

You will be greeted by the interactive session:
```text
╭────────────────────────────────────────────────╮
│  🧠 Basic Memory Helper (bmh)                  │
│  Smart discovery & structured card inspector   │
╰────────────────────────────────────────────────╯

What would you like to do?
  [1] 🔍 Search notes (by title or content)
  [2] ⚡ View active tasks (current commitments)
  [3] 📚 Browse by project (kancil / kensho)
  [4] 🕒 View recent notes
  [5] 🔄 Update bmh (pull latest release)
  [0] 🚪 Exit
```

### Piped Card Formatter
You can also pipe raw JSON from `bm` or any tool into `bmh` to format it into cards:
```bash
bm tool search-notes --type task --json | bmh
```

---

## 🗂️ Card View Structure

Every note retrieved is structured as a rich Markdown card:
- **Header**: `📌 [Index/Total] Note Title`
- **Body**: Syntax-highlighted Markdown content, observation badges (`[decision]`, `[insight]`, `[risk]`, `[todo]`), steps (`☑`, `☐`), and linked relations (`[[...]]`)
- **Footer**: `entity: <permalink>` and `external_id: <uuid>`

---

## 🛠️ Development & Agent Handbook

- **AI Agent Handbook**: See [`AGENTS.md`](./AGENTS.md) for architecture, invariants, and guidelines.
- **Contribution Guidelines**: See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for Git Flow and Conventional Commits.
