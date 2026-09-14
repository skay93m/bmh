# bmh (Basic Memory Helper)

An interactive, user-story-driven companion for **Basic Memory** (`bm`).

`bmh` streamlines Basic Memory workflows:
1. **Fixes Inputs**: Interactive prompts and clean queries (no memorizing verbose CLI flags).
2. **Fixes Outputs**: Formats notes into readable, structured cards (Header, Body, and Footer metadata).

---

## Installation

```bash
cd ~/.bmh
make install
```

This symlinks `~/.bmh/bin/bmh` to `~/.local/bin/bmh`. Any edits in `~/.bmh` take effect immediately.

---

## Usage

### 1. Interactive Mode (Default)
Simply run:
```bash
bmh
```
This launches the interactive search wizard:
- 🔍 Search notes (by keyword or title)
- ⚡ Active Tasks (`--type task --status active`)
- 📚 Browse by Project (`kancil`, `kensho`)
- 🏷️ Custom filters

### 2. Direct CLI Commands
```bash
# Keyword search
bmh "Daily Token Spend"

# Search in note titles
bmh --title "kancil"

# Filter active tasks in project kancil
bmh --project kancil --type task --status active

# Pipe from other tools / bm
bm tool search-notes --title "kancil" --json | bmh
```

---

## Card View Structure

Each note is rendered cleanly as:
- **Header**: `📌 [Index/Total] Note Title`
- **Body**: Complete Markdown content / observations / steps
- **Footer**: `External ID`, `Entity permalink`, `File path`, `Timestamp`
