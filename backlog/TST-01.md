---
id: TST-01
name: tests/conftest.py — Mock Fixtures
epic: Epic 5 - Tests
status: [x] Done
summary: Shared pytest fixtures providing mock ClickHouse and mock ChromaDB clients scoped to the pre-migration schema state. All tests run without live DB or LLM connections.
---

# TST-01 — tests/conftest.py — Mock Fixtures

- Epic: Epic 5 - Tests
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L173)

## Objective

Provide the shared fixtures that make every other test in the suite runnable without live services (ClickHouse, ChromaDB, OpenAI). All mock state reflects the pre-migration schema (field: `merged UInt8`).

## Description

`tests/conftest.py` defines two fixtures used across all test marks:

**`mock_clickhouse_client`** — returns a `MagicMock` whose `.query().named_results()` returns two pre-migration ghost contributor rows for `kubernetes/kubernetes`. Used by `run_sql_core` tests.

**`mock_chroma_client`** — returns a `MagicMock` whose `.get_collection(name).query()` returns pre-migration schema chunks (`merged UInt8`, `merged = 1` predicates). Used by `vector_search_core` tests.

Both fixtures replace the respective `_get_client()` helpers in the agents via `unittest.mock.patch`, so no live service connection is attempted.

## Scope

- `tests/conftest.py` — both fixtures with pre-migration schema state.

## Out Of Scope

- Post-migration fixtures (added in TST-05/06 as inline fixture overrides).
- Post-sync fixtures (added in TST-07/08).
- Any test functions.

## Deliverables

- `tests/conftest.py` with `mock_clickhouse_client` and `mock_chroma_client`.

## Acceptance Criteria

- Both fixtures are importable and usable with no live service running.
- `mock_clickhouse_client.query().named_results()` returns at least one row with `repo_name`, `actor_login`, `prs_opened`, `prs_merged`.
- `mock_chroma_client.get_collection("schema_docs").query()` returns a document containing `merged UInt8`.
- `mock_chroma_client.get_collection("qa_examples").query()` returns a document containing `merged = 1`.

## Dependencies

- AGT-01: `vector_search_core` must exist to know what the fixture must mock.
- AGT-02: `run_sql_core` must exist to know what the fixture must mock.

## Assumptions

- `unittest.mock` is available in the standard library — no additional test dependencies.
- Pre-migration state is the baseline; post-migration and post-sync states are layered on top in individual tests.

## Verification

```bash
# Import check
uv run python -c "from tests.conftest import mock_clickhouse_client, mock_chroma_client; print('OK')"

# Run pre_migration tests to verify fixtures work end-to-end
uv run pytest -m pre_migration -v
```

Expected:
```
tests/test_use_case.py::test_ghost_contributor_query_pre_migration PASSED
tests/test_use_case.py::test_rag_returns_correct_field_pre_migration PASSED
```

## Notes

- Completed as part of initial Epic 5 scaffolding.
- Pre-migration schema state is intentional — post-migration variants override inline where needed.
