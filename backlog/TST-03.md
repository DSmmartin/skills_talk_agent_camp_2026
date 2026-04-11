---
id: TST-03
name: test_use_case.py — @pre_migration — Ghost Contributor Query Returns Rows
epic: Epic 5 - Tests
status: [x] Done
summary: Pre-migration test verifying that the ghost contributor SQL uses `merged = 1` and returns non-empty rows via the mock ClickHouse client.
---

# TST-03 — @pre_migration — Ghost Contributor Query Returns Rows

- Epic: Epic 5 - Tests
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L181)

## Objective

Verify Act 1 baseline: the canonical ghost contributor SQL query uses the pre-migration predicate `merged = 1` and returns at least one result row from the mock client.

## Description

`test_ghost_contributor_query_pre_migration` in `tests/test_use_case.py` patches `run_sql_core`'s `_get_client` with `mock_clickhouse_client`, executes the canonical ghost contributor SQL, and asserts:

1. No error key in the JSON result.
2. `merged = 1` appears in the SQL string (pre-migration predicate).
3. `row_count > 0`.
4. `rows[0]["repo_name"] == "kubernetes/kubernetes"`.

This test is the Act 1 acceptance signal — it passes before `make migrate` and fails after if the SQL is updated to use `merged_at`.

## Scope

- `tests/test_use_case.py::test_ghost_contributor_query_pre_migration`
- Marked `@pytest.mark.pre_migration`.

## Out Of Scope

- Live ClickHouse connection (mocked).
- SQL generation by the agent (the SQL is hardcoded in the test).

## Deliverables

- `tests/test_use_case.py` with `test_ghost_contributor_query_pre_migration`.

## Acceptance Criteria

- Test passes with `pytest -m pre_migration`.
- Test asserts `merged = 1` is present in the SQL string.
- Test asserts `row_count > 0` and `rows` is non-empty.

## Dependencies

- TST-01: `mock_clickhouse_client` fixture.
- AGT-02: `run_sql_core` must be importable.

## Assumptions

- The canonical SQL is fixed in the test — it is the source of truth for the pre-migration predicate.

## Verification

```bash
uv run pytest tests/test_use_case.py::test_ghost_contributor_query_pre_migration -v
```

Expected:
```
tests/test_use_case.py::test_ghost_contributor_query_pre_migration PASSED
```

## Notes

- Completed as part of initial Epic 5 scaffolding.
- This test must still pass after TST-08 (post-sync) — the pre-migration path is unchanged by schema_sync.
