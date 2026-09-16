# Orchestration Plan: bmh Tri-Modal CLI Architecture

## Overview
Implement the Tri-Modal (Ingest, Query, Lint) interactive CLI architecture for `bmh` per requirements R1-R5 and acceptance criteria in `/Users/kancil/.bmh/.agents/ORIGINAL_REQUEST.md`.

## Execution Phases

### Phase 0: Survey & Scope Mapping
- Dispatch 3 parallel explorers/spec miners:
  - Explorer 1 (`survey_explorer_1`): Survey existing `bmh` repository structure, dependencies, CLI entry points, current tests, and configs.
  - Explorer 2 (`survey_explorer_2`): Investigate `bm` CLI command specifications, arguments, output formats, and expected contracts.
  - Spec Miner 1 (`survey_spec_miner_1`): Map requirements R1-R5 to concrete code artifacts, interfaces, and acceptance tests.
- Consolidate findings into `/Users/kancil/.bmh/PROJECT.md` with Feature Inventory and architecture contracts.

### Phase 1: Dual Track Launch
- Track 1: E2E Testing Track (opaque-box, requirement-driven 4-tier test suite generating `TEST_READY.md`).
- Track 2: Implementation Track (Milestones M1 through M5).

### Phase 2: Implementation Milestones
- **M1: Subprocess Execution & UI Primitives** (`src/bmh/core/client.py`, `src/bmh/ui/cards.py`)
- **M2: Ingest Hub** (`src/bmh/workflows/ingest.py`, 5 templates, appender, piped capture)
- **M3: Query Hub & Guided Query Co-Pilot** (`src/bmh/workflows/query.py`)
- **M4: Lint Hub & Health Diagnostics** (`src/bmh/workflows/lint.py`)
- **M5: Tri-Modal Interactive Gateway & Navigation** (interactive menu, piped JSON handling, update, exit)

### Phase 3: Final Verification & Hardening (Milestone M6)
- Pass 100% E2E tests and unit tests (`uv run pytest`)
- Run `uv tool install . --force`
- Run Forensic Auditor verification (CLEAN required)
- Reviewers and Challengers gate checks
- Final victory claim and human report to caller/user
