---
id: TST-06
name: test_use_case.py — @post_migration — RAG Still Returns Stale merged Chunk
epic: Epic 5 - Tests
status: [x] Done
summary: Post-migration test verifying that the RAG tool still returns the stale `merged UInt8` chunk before schema_sync has run — showing the second layer of the silent failure.
---

# TST-06 — @post_migration — RAG Still Returns Stale merged Chunk

- Epic: Epic 5 - Tests
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L184)

## Objective

Show the second layer of the post-migration silent failure: ChromaDB still has the pre-migration chunk, so the RAG tool confidently returns stale context describing `merged UInt8` even after the DB has been migrated.

## Description

`test_rag_returns_stale_chunk_post_migration` uses the same `mock_chroma_client` from `conftest.py` (which is intentionally seeded with pre-migration content — reflecting that `make migrate` does NOT update ChromaDB chunks, only marks them `stale: True`).

The test asserts:
1. `"merged"` is still present in the returned RAG context.
2. `"merged_at"` is NOT present (chunk has NOT been updated yet).

This test captures the "four layers broken" state before any skill is applied. The contrast with TST-07 shows what schema_sync fixes in ChromaDB.

## Scope

- `tests/test_use_case.py::test_rag_returns_stale_chunk_post_migration`
- Marked `@pytest.mark.post_migration`.

## Out Of Scope

- Live ChromaDB connection (mocked).
- The `stale: True` metadata flag (tested separately in TST-07).

## Deliverables

- `tests/test_use_case.py` with `test_rag_returns_stale_chunk_post_migration`.

## Acceptance Criteria

- Test is marked `@pytest.mark.post_migration`.
- Test uses the same `mock_chroma_client` as TST-04 (same stale content — migration did not update chunks).
- Test asserts `"merged"` is in the context and `"merged_at"` is absent.

## Dependencies

- TST-01: `mock_chroma_client` fixture (same fixture — stale content is intentional here).
- AGT-01: `vector_search_core` must be importable.

## Assumptions

- The `mock_chroma_client` in `conftest.py` intentionally reflects the pre-migration / stale-chunk state.
- No separate post-migration fixture override is needed for this test.

## Verification

```bash
uv run pytest tests/test_use_case.py::test_rag_returns_stale_chunk_post_migration -v
```

Expected:
```
tests/test_use_case.py::test_rag_returns_stale_chunk_post_migration PASSED
```

## Notes

- Together with TST-05, this test documents the two visible symptoms of Act 2.
- TST-07 is the "after skill" counterpart — it verifies all four layers are fixed.
