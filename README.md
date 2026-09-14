# bmh (Basic Memory Helper)

A purely interactive companion for **Basic Memory** (`bm`).

Instead of memorizing flags, `bmh` provides a guided walkthrough for searching and exploring your knowledge base, formatting every result in clean, structured cards.

---

## Installation

```bash
cd ~/.bmh
make install
```

Symlinks `~/.bmh/bin/bmh` to `~/.local/bin/bmh`.

---

## Usage

Simply run:
```bash
bmh
```

`bmh` will launch an interactive session:
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
  [0] 🚪 Exit
```

### Piped Card Formatter
You can also pipe any Basic Memory JSON query directly into `bmh`:
```bash
bm tool search-notes --type task --json | bmh
```

---

## Card View Structure

Each note is rendered cleanly as:
- **Header**: `📌 [Index/Total] Note Title`
- **Body**: Complete Markdown content / observations / steps
- **Footer**: `External ID`, `Entity permalink`, `File path`, `Timestamp`
