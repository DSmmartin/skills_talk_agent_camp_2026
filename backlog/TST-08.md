---
id: TST-08
name: test_schema_sync.py — @schema_sync — Skill Outcome: Query Returns Correct Rows
epic: Epic 5 - Tests
status: [x] Done
summary: Skill outcome contract test. After schema_sync, the ghost contributor query uses merged_at IS NOT NULL and returns non-empty rows. End-to-end validation of Act 3.
---

# TST-08 — @schema_sync — Skill Outcome: Query Returns Correct Rows After Sync

- Epic: Epic 5 - Tests
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L186)

## Objective

Verify the end-to-end Act 3 recovery: after any schema-sync skill has been applied, the ghost contributor SQL uses `merged_at IS NOT NULL` (not `merged = 1`) and returns correct rows.

## Description

`test_query_correct_rows_after_sync` in `tests/test_schema_sync.py` uses a post-sync mock ClickHouse client that returns ghost contributor rows when `merged_at IS NOT NULL` is used in the query.

The test:
1. Reads the NL2SQL system prompt directly from disk (`agents_core/nl2sql/prompts/system.md`).
2. Asserts that the prompt no longer contains `merged = 1`.
3. Constructs the post-migration SQL (using `merged_at IS NOT NULL`).
4. Patches `_get_client` with `mock_clickhouse_client_post_sync`.
5. Calls `run_sql_core(post_migration_sql)` and asserts `row_count > 0`.

This test closes the loop on Act 3: the same ghost contributor question that returned 0 rows in Act 2 now returns correct results.

## Scope

- `tests/test_schema_sync.py::test_query_correct_rows_after_sync`
- Marked `@pytest.mark.schema_sync`.

## Out Of Scope

- The agent generating the SQL (SQL is constructed inline in the test).
- Live ClickHouse connection (mocked).

## Deliverables

- `tests/test_schema_sync.py` with `test_query_correct_rows_after_sync`.
- Inline `mock_clickhouse_client_post_sync` fixture returning non-empty rows for `merged_at IS NOT NULL` queries.

## Acceptance Criteria

- Test is marked `@pytest.mark.schema_sync`.
- Test reads the NL2SQL prompt from disk and asserts `merged = 1` is absent.
- Post-migration SQL uses `merged_at IS NOT NULL`.
- Mock client returns non-empty rows for the post-migration SQL.
- `row_count > 0` in the result.

## Dependencies

- TST-07: Layer-level checks (TST-08 is the end-to-end complement).
- AGT-02: `run_sql_core` must be importable.
- DEV-08: NL2SQL prompt file must be patched (this test reads the file directly).

## Assumptions

- The NL2SQL prompt has already been patched before this test runs (either by a skill or `schema_sync.py`).
- The post-sync mock client returns results only for the `merged_at IS NOT NULL` predicate (simulating the post-migration DB state).

## Verification

```bash
# After running schema_sync or a skill:
uv run pytest tests/test_schema_sync.py::test_query_correct_rows_after_sync -v -m schema_sync
```

Expected:
```
tests/test_schema_sync.py::test_query_correct_rows_after_sync PASSED
```

## Notes

- This is the "show stopper" Act 3 test: the answer is correct again.
- Together with TST-07, forms the skill outcome contract for the entire demo.
- Run TST-05 first to show the broken state, then TST-08 to show the fix.
