# E2E Test Infra: bmh Tri-Modal CLI Architecture

## Test Philosophy
- Opaque-box, requirement-driven. Derived from `/Users/kancil/.bmh/.agents/ORIGINAL_REQUEST.md` and `PROJECT.md`.
- No reliance on internal implementation details; exercise CLI through Typer CliRunner, piped streams, and direct high-level workflows with mockable `BMClient` subprocess boundaries.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial + Real-World Workloads.

## Feature Inventory Mapping
| # | Feature | Requirement | Tier 1 | Tier 2 | Tier 3 |
|---|---------|-------------|:------:|:------:|:------:|
| 1 | BMClient Subprocess Core | R5 | 5 | 5 | ✓ |
| 2 | Model Definitions & Serialization | R5 | 5 | 5 | ✓ |
| 3 | Observation Badge Formatting | R5 | 5 | 5 | ✓ |
| 4 | Diagnostic Result Panels | R5 | 5 | 5 | ✓ |
| 5 | Task Note Template Wizard | R2 | 5 | 5 | ✓ |
| 6 | Insight Note Template Wizard | R2 | 5 | 5 | ✓ |
| 7 | Meeting Note Template Wizard | R2 | 5 | 5 | ✓ |
| 8 | Decision Note Template Wizard | R2 | 5 | 5 | ✓ |
| 9 | Scratchpad Note Template Wizard | R2 | 5 | 5 | ✓ |
| 10 | Quick Observation Appender | R2 | 5 | 5 | ✓ |
| 11 | Piped Ingest Handler | R2 | 5 | 5 | ✓ |
| 12 | Note Search Browser | R3 | 5 | 5 | ✓ |
| 13 | Active Task Inspector & Step Checkoff | R3 | 5 | 5 | ✓ |
| 14 | Project Browser (kancil/kensho) | R3 | 5 | 5 | ✓ |
| 15 | Recent Activity Timeline | R3 | 5 | 5 | ✓ |
| 16 | Detail Note Reader | R3 | 5 | 5 | ✓ |
| 17 | Guided Query Co-Pilot Interview | R3 | 5 | 5 | ✓ |
| 18 | Co-Pilot Execution & Presentation | R3 | 5 | 5 | ✓ |
| 19 | Schema Validator Diagnostic | R4 | 5 | 5 | ✓ |
| 20 | Orphan Link Inspector | R4 | 5 | 5 | ✓ |
| 21 | Sync & Index Doctor | R4 | 5 | 5 | ✓ |
| 22 | Schema Drift Analyzer | R4 | 5 | 5 | ✓ |
| 23 | 'Lint All' Unified Dashboard | R4 | 5 | 5 | ✓ |
| 24 | Tri-Modal Gateway Menu | R1 | 5 | 5 | ✓ |
| 25 | Piped JSON Stream Handling | R1 | 5 | 5 | ✓ |
| 26 | Graceful Error Shielding | R1 | 5 | 5 | ✓ |
| 27 | Update & Exit Integration | R1 | 5 | 5 | ✓ |

## Test Architecture
- Test runner: `uv run pytest tests/e2e -v`
- Location: `tests/e2e/`
  - `tests/e2e/test_tier1_features.py` — Tier 1 Feature Coverage
  - `tests/e2e/test_tier2_boundaries.py` — Tier 2 Boundary & Corner Cases
  - `tests/e2e/test_tier3_pairwise.py` — Tier 3 Cross-Feature Interactions
  - `tests/e2e/test_tier4_scenarios.py` — Tier 4 Real-World Application Scenarios
- Mocking & Isolation:
  - Tests use mocked `BMClient` or isolated temporary test environments so live host projects are not modified.
  - Subprocess exit codes, JSON outputs, and stdout streams match the exact contracts documented in `PROJECT.md` and `survey_explorer_2/report.md`.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full Task Lifecycle | Ingest Task Wizard -> Browse Active Tasks -> Checkoff Step -> Lint Verification | High |
| 2 | Research & Insight Ingestion | Piped Ingest -> Observation Appender -> Co-Pilot Retrieval -> Detail Reader | High |
| 3 | Project Health Audit | Lint All Dashboard -> Schema Diff -> Orphan Fix -> Doctor Verification | High |
| 4 | Meeting Notes to Decisions | Meeting Wizard -> Decision Wizard -> Project Browser (kancil/kensho) | Medium |
| 5 | Piped Stream CLI Pipeline | Piped JSON Stream -> Rich Card Formatting -> Error Shielding on Bad JSON | Medium |

## Coverage Thresholds
- Tier 1: >=5 test cases per feature
- Tier 2: >=5 boundary test cases per feature
- Tier 3: Pairwise combinations across hubs (Ingest <-> Query, Query <-> Lint, Ingest <-> Lint)
- Tier 4: >=5 realistic end-to-end user application scenarios
