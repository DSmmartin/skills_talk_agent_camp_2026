---
id: IMP-06
name: Document Local Seed Expected Results and Schema Upgrade Gate in AUDIENCE_GUIDE
epic: Epic 8 - Improvements
status: [x] Done
summary: Add verified per-act expected query results for the local dataset and document the schema_upgrade_gate test in AUDIENCE_GUIDE.md.
---

# IMP-06 - Document Local Seed Expected Results and Schema Upgrade Gate in AUDIENCE_GUIDE

- Epic: Epic 8 - Improvements
- Priority: P1
- Estimate: S
- Status: [x] Done
- Source: PRODUCT_BACKLOG.md

## Objective

Give workshop participants concrete, verifiable numbers for each act of the demo when running with the local 18-row dataset, and explain the `schema_upgrade_gate` test so they understand its intentional failure in Act 2 and expected pass in Act 3.

## Description

Two additions to `AUDIENCE_GUIDE.md`:

**1. Expected results tables (local seed, Section 5)**
Workshop participants need to know what the agent should return at each act when `LOCAL_SEED=true`. Without a reference, a wrong answer looks the same as a correct one. The tables document the exact numbers verified by running queries directly against the live local ClickHouse instance.

**2. Schema upgrade gate documentation (Section 10)**
`tests/test_schema_upgrade_gate.py` is a strict readiness gate that checks all four layers (YAML contract, NL2SQL prompt, RAG prompt, agent tool description) for post-migration field names. It is explicitly designed to fail in the pre-migration state and pass only after `make schema-sync`. Without documentation, participants may think the test failure is a bug. The guide must explain the lifecycle: fail in Act 2, pass in Act 3.

## Scope

- `AUDIENCE_GUIDE.md` Section 5 (local seed callout): add dataset overview table, full contributor table, and per-act expected output for Act 1 (4 ghost contributors), Act 2 (0 rows — silent failure), and Act 3 (same 4 rows via `merged_at IS NOT NULL`).
- `AUDIENCE_GUIDE.md` Section 10 (Running the Tests): add `### Special test: schema_upgrade_gate` subsection with command, Act 2 expected failure output (5 named failures), Act 3 expected pass output, and explanation of why it is excluded from CI.
- `AUDIENCE_GUIDE.md` Section 13 (Reference): add `schema_upgrade_gate` row to the Tests command table.

## Out Of Scope

- Changing any code or SQL files.
- Adding a `local_seed` variant of the test suite.
- Modifying `tests/README.md` (it already covers the gate adequately).

## Deliverables

- Updated `AUDIENCE_GUIDE.md` with local-seed result tables in Section 5 and upgrade gate documentation in Sections 10 and 13.

## Acceptance Criteria

- Section 5 local seed callout contains three tables: dataset overview, all-contributors breakdown, and per-act expected output.
- Section 10 contains a `schema_upgrade_gate` subsection with the exact command, Act 2 failure listing, and Act 3 pass message.
- Section 13 test reference table includes the gate command.
- All expected numbers in the tables match live query results from the verified local dataset (18 rows, 4 ghost contributors).

## Dependencies

- IMP-04 must be complete so the local dataset is correct before numbers are recorded.

## Assumptions

- Expected results are documented against the pre-migration schema state (`merged UInt8`) and are accurate for Acts 1, 2, and 3 as described.
- The Act 2 gate failure list (5 items) is stable and will not change unless the prompt files or YAML schema are modified.

## Verification

All numbers verified by direct `clickhouse_connect` query against the live local ClickHouse container after `make seed LOCAL=1`.

## Notes

- Completed 2026-04-09.
- The dataset overview table and contributor breakdown are derived from live queries, not from reading the SQL file, to ensure correctness.
