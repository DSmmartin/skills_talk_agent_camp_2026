---
id: TST-05
name: test_use_case.py — @post_migration — Query Returns 0 Rows After Migration
epic: Epic 5 - Tests
status: [x] Done
summary: Post-migration test verifying the silent failure: the same ghost contributor SQL with `merged = 1` returns 0 rows after `make migrate`, with no exception thrown.
---

# TST-05 — @post_migration — Query Returns 0 Rows After Migration

- Epic: Epic 5 - Tests
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L183)

## Objective

Demonstrate the silent failure at the test level: after migration, the canonical SQL with `merged = 1` returns zero rows. No exception is raised — the agent just returns an empty result, silently.

## Description

`test_ghost_contributor_query_post_migration` uses an inline fixture override that returns a mock ClickHouse client simulating the post-migration state — `merged` column exists but all values are `0` (zeroed-out by `migrate_schema.py`), so `countIf(action = 'closed' AND merged = 1)` produces `0` for every row.

The test uses the same SQL as TST-03 (with `merged = 1`) and asserts:
1. No error is raised (silent failure — not an exception).
2. `row_count == 0` OR all `prs_merged` values are `0`.

This test documents the exact failure mode shown in Act 2 of the demo.

## Scope

- `tests/test_use_case.py::test_ghost_contributor_query_post_migration`
- Marked `@pytest.mark.post_migration`.

## Out Of Scope

- Live ClickHouse connection (mocked).
- SQL generation or agent reasoning.

## Deliverables

- `tests/test_use_case.py` with `test_ghost_contributor_query_post_migration`.
- Inline `mock_clickhouse_client_post_migration` fixture (or fixture override).

## Acceptance Criteria

- Test is marked `@pytest.mark.post_migration`.
- Mock client returns rows where `prs_merged = 0` for every row.
- Test asserts no exception is raised.
- Test asserts zero merged PRs are found (the silent failure).

## Dependencies

- TST-01: Base fixtures in `conftest.py` as reference for the post-migration override.
- AGT-02: `run_sql_core` must be importable.
- MIG-05: Verified that `merged = 1` returns 0 rows silently (confirmed at SQL level).

## Assumptions

- The post-migration mock does not raise an exception — it returns rows with all `prs_merged = 0`.
- The SQL string itself is unchanged from TST-03 (still uses `merged = 1`).

## Verification

```bash
uv run pytest tests/test_use_case.py::test_ghost_contributor_query_post_migration -v
```

Expected:
```
tests/test_use_case.py::test_ghost_contributor_query_post_migration PASSED
```

## Notes

- Act 2 key moment: same question, same SQL, zero rows, zero exceptions.
- Contrast with TST-08: after schema_sync, the same fixture with `merged_at IS NOT NULL` returns rows again.
