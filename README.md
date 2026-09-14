# bmh (Basic Memory Helper)

A purely interactive companion for **Basic Memory** (`bm`).

Instead of memorizing flags and parsing unformatted JSON, `bmh` provides a guided walkthrough for searching and exploring your knowledge base, rendering every result in clean, structured cards.

---

## 🚀 Quick Install (Any Mac / Linux)

Run this one-liner in your terminal:

```bash
git clone https://github.com/skay93m/bmh.git ~/.bmh && cd ~/.bmh && make install
```

> **Note**: Ensure `~/.local/bin` is in your `$PATH` (if not already):
> ```bash
> echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
> source ~/.zshrc
> ```

---

## 🔄 Updating to Latest Version

On any machine with `bmh` installed, run:
```bash
bmh update
```
*(Or select option `[5]` from the interactive menu).*

---

## 📖 Usage

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
  [5] 🔄 Update bmh (pull latest from GitHub)
  [0] 🚪 Exit
```

### Piped Card Formatter
You can also pipe raw JSON from `bm` or any tool into `bmh` to format it into cards:
```bash
bm tool search-notes --type task --json | bmh
```

---

## 🗂️ Card View Structure

Every note retrieved is structured as a readable card:
- **Header**: `📌 [Index/Total] Note Title`
- **Body**: Full Markdown content, observations (`[decision]`, `[insight]`), steps (`[x]`, `[ ]`), and relations (`[[...]]`)
- **Footer**: `External ID`, `Entity permalink`, `File path`, and formatted `Timestamp`

---

## 🛠️ Development & Agent Handbook

- **AI Agent Handbook**: See [`AGENTS.md`](./AGENTS.md) for full context, invariants, and architecture.
- **Contribution Guidelines**: See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for Git Flow and Conventional Commits.
