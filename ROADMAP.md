# bmh Product Roadmap & Agile Operating System

---

## 🌟 North Star

**To provide a zero-friction, zero-context-pollution interactive memory operating layer for human operators and AI agents, turning Basic Memory into an intuitive, high-velocity second brain.**

---

## 🎯 Strategic Horizons (Roadmap to Value)

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│     HORIZON 1 (Now)     │ ──► │    HORIZON 2 (Next)     │ ──► │    HORIZON 3 (Later)    │
│  Interactive Discovery  │     │ Note Capture & Progress │     │   Progressive Context   │
│   & Compact Cards (✅)   │     │    Authoring Wizards    │     │   & Graph Traversal     │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

### 🔴 Horizon 1: Now (Core Discovery & Presentation) — `v1.0.x` [SHIPPED]
- [x] **Interactive Search Walkthrough**: Pure TUI menu for keywords, titles, and project filters.
- [x] **Compact Rich Cards**: Header, Markdown body, and footer with `entity` and `external_id` only.
- [x] **Self-Update Engine**: `bmh update` and interactive menu option to pull latest releases.
- [x] **Cross-Architecture Installer**: Native Apple Silicon (`arm64`) and Intel (`x86_64`) support with zero Xcode/make dependencies.
- [x] **Developer & Agent Handbooks**: `AGENTS.md`, `CONTRIBUTING.md`, Commitizen conventions.

---

### 🟡 Horizon 2: Next (Capture, Authoring & Task Progression) — `v1.1.x`
- [ ] **Interactive Note Capture Wizard**:
  - Structured templates for `Task`, `Observation/Insight`, `Meeting/Log`, and `Decision`.
  - Auto-formatting canonical frontmatter, observations (`[decision]`, `[risk]`, `[insight]`), and relations (`[[...]]`).
- [ ] **Task Step Progression**:
  - Interactive picker to view active tasks and mark checkboxes complete (`[ ]` -> `[x]`).
  - Append quick observations directly from the terminal without manual file editing.
- [ ] **Note Detail Pager / Reader**:
  - Interactive reader to inspect specific notes in full with optional Markdown highlighting.

---

### 🟢 Horizon 3: Later (Progressive Context & Graph Traversal) — `v1.2.x`
- [ ] **Token-Slim Context Extraction**:
  - Bundle target note + 1-hop relations (`governed_by`, `relates_to`) into dense, minified context for LLM prompts.
- [ ] **Graph Traversal Inspector**:
  - Browse relations interactively (navigate between linked notes).
- [ ] **MCP & Sidecar Integration**:
  - Expose `bmh` formatters and context tools directly to OpenClaw / agent runtimes.

---

## ⚖️ Execution Constraints & Capacity

- **Work-In-Progress Limit**: Maximum **3 active project increments** at any one time to maintain velocity and code quality.
- **Invariants**:
  - 100% interactive walkthroughs (no required flags).
  - Zero context pollution (dense, high-signal terminal outputs).
  - Strict Git Flow (`main` = stable tagged releases, `develop` = integration).
