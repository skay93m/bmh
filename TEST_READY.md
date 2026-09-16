# TEST_READY: 4-Tier Requirement-Driven E2E Test Suite for `bmh`

**Date:** 2026-09-16  
**Author:** Test Writer 1 (E2E Testing Track)  
**Status:** COMPLETE & VERIFIED  
**Verification Command:** `uv run pytest tests/e2e -v`  
**Test Suite Results:** 198 tests collected (100 passed, 98 progressively skipped, 0 failed, 0 errors)

---

## 1. Executive Summary

The comprehensive, opaque-box, requirement-driven 4-tier E2E test suite for the `bmh` Tri-Modal CLI architecture has been created and verified in `tests/e2e/`.

The test suite strictly adheres to:
- **Progressive Testability**: Features currently implemented or foundational run and pass immediately (100 passing tests); features pending in future milestones (M2 Ingest, M3 Query, M4 Lint, M5 Gateway) are cleanly gated with informative skip indicators, automatically unlocking as workers complete their milestones.
- **Isolation & Safety**: All `bm` subprocess boundaries are isolated and mocked. Live databases (`kancil`, `kensho`) are protected via an active subprocess execution guard in `tests/e2e/conftest.py`.
- **Requirements-Driven & Opaque-Box**: Tests are derived strictly from authoritative requirements in `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`, and the survey reports.

---

## 2. Test Architecture & Directory Layout

```
tests/e2e/
├── conftest.py               # Shared fixtures, mock BMClient, and live subprocess guard
├── test_tier1_features.py    # Tier 1: Feature Coverage (Features 1-27)
├── test_tier2_boundaries.py  # Tier 2: Boundary Value Analysis & Edge Cases
├── test_tier3_pairwise.py    # Tier 3: Cross-Hub Pairwise Combinations
└── test_tier4_scenarios.py   # Tier 4: 5 Real-World Application Scenarios
```

---

## 3. Tier Breakdown & Coverage

### Tier 1: Feature Coverage (`tests/e2e/test_tier1_features.py`)
Covers all 27 features identified in `PROJECT.md` and `TEST_INFRA.md`:
1. `BMClient` Subprocess Core (11 test cases)
2. Model Definitions & Serialization (7 test cases)
3. Observation Badge Formatting (6 test cases)
4. Diagnostic Result Panels (6 test cases)
5. Task Note Template Wizard (5 test cases)
6. Insight Note Template Wizard (5 test cases)
7. Meeting Note Template Wizard (5 test cases)
8. Decision Note Template Wizard (5 test cases)
9. Scratchpad Note Template Wizard (5 test cases)
10. Quick Observation Appender (5 test cases)
11. Piped Ingest Handler (5 test cases)
12. Note Search Browser (5 test cases)
13. Active Task Inspector & Step Checkoff (5 test cases)
14. Project Browser (kancil/kensho) (5 test cases)
15. Recent Activity Timeline (5 test cases)
16. Detail Note Reader (5 test cases)
17. Guided Query Co-Pilot Interview (5 test cases)
18. Co-Pilot Execution & Presentation (5 test cases)
19. Schema Validator Diagnostic (5 test cases)
20. Orphan Link Inspector (5 test cases)
21. Sync & Index Doctor (5 test cases)
22. Schema Drift Analyzer (5 test cases)
23. 'Lint All' Unified Dashboard (5 test cases)
24. Tri-Modal Gateway Menu (5 test cases)
25. Piped JSON Stream Handling (5 test cases)
26. Graceful Error Shielding (5 test cases)
27. Update & Exit Integration (5 test cases)

### Tier 2: Boundary Value Analysis & Edge Cases (`tests/e2e/test_tier2_boundaries.py`)
Covers boundary conditions across 6 comprehensive categories (33 test cases):
- **Empty & Whitespace Inputs**: Empty query, whitespace query, empty piped stdin, whitespace newlines, blank/None titles, empty note content, empty search result renderers.
- **Extreme Inputs & Special Characters**: HTML/XSS character preservation, markdown bracket escaping (`\[decision]`), large 20KB+ note payloads, regex pattern meta-characters (`[0-9]+.*`), malformed JSON stream fallback, JSON primitive numbers/booleans.
- **Subprocess Error Modalities**: Missing `bm` binary (`BMNotFoundError`), timeout translation (`BMError`), read-note exit 0 with null fields, schema-validate exit 0 with error dictionary, schema-diff exit 0 with missing schema dictionary, orphans exit 1 project not found, doctor failure exit 1.
- **Task Step Checkoff Boundaries**: Empty markdown without checkboxes, markdown without steps, all steps already completed (`[x]`), mixed whitespace/cases (`[X]`, `[x]`, `[ ]`), duplicate step name resolution.
- **Lint Scoring Boundaries**: Perfect score 100/100 (Grade A), negative calculation clamped to 0 (Grade F), letter grade thresholds (A, B, C, F).
- **Navigation & Signals**: Invalid menu choice re-prompting, `KeyboardInterrupt` (`Ctrl+C`) clean exit, `EOFError` (`Ctrl+D`) clean exit, ISO timestamp parser resilience.

### Tier 3: Pairwise Cross-Hub Combinations (`tests/e2e/test_tier3_pairwise.py`)
Covers combinatorial interactions across hubs (15 test cases):
- **Ingest <-> Query**: Task wizard ingest -> Search notes retrieval; Piped ingest -> Detail note reader; Query search -> Quick observation appender; Kensho insight ingest -> Kensho project browser; Meeting notes with action items -> Active tasks discovery.
- **Query <-> Lint**: Active task step checkoff -> Schema validate; Project browser unlinked note -> Orphan inspector; Co-Pilot retrieved note -> Schema drift analyzer; Recent activity timeline -> Sync doctor consistency.
- **Ingest <-> Lint**: Decision note ingest -> Schema validator; Piped ingest -> Sync doctor; Scratchpad ingest -> Lint all dashboard.
- **Gateway <-> Hubs**: Gateway navigation to search, active tasks, and project browser with clean returns and exits.

### Tier 4: Real-World Application Scenarios (`tests/e2e/test_tier4_scenarios.py`)
Covers the 5 canonical user workflows specified in `TEST_INFRA.md`:
1. **Full Task Lifecycle**: Task Wizard Ingest -> Active Tasks Inspector -> Step Checkoff (`[ ]` -> `[x]`) -> Lint Schema Validation.
2. **Research & Insight Ingestion**: Piped Ingest -> Quick Observation Appender -> Guided Co-Pilot Retrieval -> Detail Note Reader.
3. **Project Health Audit**: Lint All Diagnostic Dashboard -> Schema Drift Analyzer -> Orphan Inspector Verification -> Sync Doctor Verification.
4. **Meeting Notes to Decisions**: Meeting Wizard -> Decision Wizard (ADR creation) -> Project Browser (`kancil`/`kensho`).
5. **Piped Stream CLI Pipeline**: Piped JSON search result stream -> Rich card formatting -> Raw text fallback -> Empty stream handling.

---

## 4. Verification Instructions

To execute the entire E2E test suite:

```bash
uv run pytest tests/e2e -v
```

To run individual tiers:

```bash
uv run pytest tests/e2e/test_tier1_features.py -v
uv run pytest tests/e2e/test_tier2_boundaries.py -v
uv run pytest tests/e2e/test_tier3_pairwise.py -v
uv run pytest tests/e2e/test_tier4_scenarios.py -v
```

---

## 5. Status for Implementation Workers (M1–M5) & M6 Verifier

- **Worker M1** (Subprocess & UI Foundation): Feature 1 (`BMClient` primitives) and Feature 2 (`models`) tests are active and passing. Panel renderer tests in Feature 4 will automatically activate when `ui/cards.py` diagnostic functions are exposed.
- **Worker M2** (Ingest Hub): Implement `bmh.workflows.ingest` (`run_note_wizard`, `run_quick_appender`, `handle_piped_capture`). All Ingest tests in Tiers 1-4 will automatically run against the implementation.
- **Worker M3** (Query Hub & Co-Pilot): Implement `bmh.workflows.query` (`run_active_tasks_inspector`, `run_recent_timeline`, `run_detail_reader`, `run_guided_copilot`). All Query tests in Tiers 1-4 will automatically run.
- **Worker M4** (Lint Hub & Diagnostics): Implement `bmh.workflows.lint` (`run_schema_validator`, `run_orphan_inspector`, `run_sync_doctor`, `run_schema_drift`, `run_lint_all`). All Lint tests in Tiers 1-4 will automatically run.
- **Worker M5** (Gateway & Navigation): Integrate Tri-Modal gateway menu in `bmh.ui.menu` / `bmh.main`.
- **Milestone 6 Verifier**: Run `uv run pytest tests/e2e` to verify 100% passing rate with 0 skips across all 198 tests.
