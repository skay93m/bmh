# Canonical Backlog — bmh

This backlog tracks user stories across epics, prioritised according to the [Roadmap](./ROADMAP.md).

---

## 🏛️ Epic Taxonomy

- **EPIC-1: Search & Knowledge Discovery** (`epic:search`)
- **EPIC-2: Note Capture & Authoring Wizard** (`epic:capture`)
- **EPIC-3: Task Advancement & Progression** (`epic:task-progress`)
- **EPIC-4: Progressive Context Extraction** (`epic:context`)
- **EPIC-5: Multi-Platform DX & Distribution** (`epic:dx`)

---

## 📋 Backlog Items

### 🔴 Horizon 1: Core Discovery (Complete)

| ID | Epic | User Story | Status |
| :--- | :--- | :--- | :--- |
| **STORY-001** | `epic:search` | **Interactive Search Wizard**: As an operator, I want to search notes interactively by title or keyword without memorising CLI flags. | `DONE` (v1.0.0) |
| **STORY-002** | `epic:search` | **Compact Rich Card Formatter**: As an operator/agent, I want retrieved notes displayed in compact cards with `entity` and `external_id` only in the footer. | `DONE` (v1.0.3) |
| **STORY-003** | `epic:dx` | **Self-Update Engine**: As a user on secondary machines, I want `bmh update` to pull the latest releases from GitHub. | `DONE` (v1.0.1) |
| **STORY-004** | `epic:dx` | **Cross-Architecture Installer**: As a user, I want `install.sh` to work on both Apple Silicon (`arm64`) and Intel (`x86_64`) without Xcode dependencies. | `DONE` (v1.0.2) |

---

### 🟡 Horizon 2: Capture & Task Progression (Sprint Candidates)

| ID | Epic | User Story | Priority | Status |
| :--- | :--- | :--- | :--- | :--- |
| **STORY-005** | `epic:capture` | **Interactive Note Capture Wizard**: As an operator, I want an interactive prompt to create notes using structured templates (Task, Insight, Meeting, Decision) with canonical frontmatter and observations. | `P0` | `Sprint Candidate` |
| **STORY-006** | `epic:task-progress` | **Task Step Checkoff**: As an operator, I want an interactive menu to view active tasks and check off steps (`[ ]` -> `[x]`) without opening files. | `P1` | `Backlog` |
| **STORY-007** | `epic:task-progress` | **Quick Observation Appender**: As an operator, I want to append an observation (`[decision]`, `[risk]`, `[insight]`) to an existing note directly from `bmh`. | `P1` | `Backlog` |
| **STORY-008** | `epic:search` | **Detail Note Reader / Pager**: As an operator, I want to select a single note from search results and open it in a clean full-screen pager. | `P2` | `Backlog` |

---

### 🟢 Horizon 3: Progressive Context & Graph Traversal (Strategic)

| ID | Epic | User Story | Priority | Status |
| :--- | :--- | :--- | :--- | :--- |
| **STORY-009** | `epic:context` | **Token-Slim Context Extraction**: As an AI agent/operator, I want to extract a note and its depth-1 relations formatted for LLM prompt injection with zero metadata noise. | `P1` | `Backlog` |
| **STORY-010** | `epic:context` | **Interactive Graph Traversal**: As an operator, I want to navigate from one note to its linked relations interactively in the terminal. | `P2` | `Backlog` |
