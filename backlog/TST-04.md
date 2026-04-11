---
id: TST-04
name: test_use_case.py — @pre_migration — RAG Returns merged UInt8 Context
epic: Epic 5 - Tests
status: [x] Done
summary: Pre-migration test verifying that the RAG tool returns context containing `merged` and `UInt8`, and does not return `merged_at`.
---

# TST-04 — @pre_migration — RAG Returns merged UInt8 Context

- Epic: Epic 5 - Tests
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L182)

## Objective

Verify that the RAG tool returns pre-migration schema context before any migration or sync has occurred — specifically that the retrieved chunk describes `merged UInt8`, not `merged_at`.

## Description

`test_rag_returns_correct_field_pre_migration` in `tests/test_use_case.py` patches `vector_search_core`'s `_get_client` with `mock_chroma_client`, calls `vector_search_core("ghost contributors merged PR")`, and asserts:

1. `"merged"` is in the returned context string.
2. `"UInt8"` is in the returned context string.
3. `"merged_at"` is NOT in the returned context string.

This verifies the baseline: the RAG layer correctly describes the pre-migration schema.

## Scope

- `tests/test_use_case.py::test_rag_returns_correct_field_pre_migration`
- Marked `@pytest.mark.pre_migration`.

## Out Of Scope

- Live ChromaDB connection (mocked).
- Embedding or vector similarity (mock returns a fixed chunk).

## Deliverables

- `tests/test_use_case.py` with `test_rag_returns_correct_field_pre_migration`.

## Acceptance Criteria

- Test passes with `pytest -m pre_migration`.
- Test asserts `"merged"` and `"UInt8"` are present in the returned context.
- Test asserts `"merged_at"` is absent.

## Dependencies

- TST-01: `mock_chroma_client` fixture.
- AGT-01: `vector_search_core` must be importable.

## Assumptions

- The mock ChromaDB client returns the pre-migration schema chunk defined in `conftest.py`.

## Verification

```bash
uv run pytest tests/test_use_case.py::test_rag_returns_correct_field_pre_migration -v
```

Expected:
```
tests/test_use_case.py::test_rag_returns_correct_field_pre_migration PASSED
```

## Notes

- Completed as part of initial Epic 5 scaffolding.
- Counterpart test TST-06 verifies that a post-migration RAG mock still returns the stale chunk (before schema_sync).
