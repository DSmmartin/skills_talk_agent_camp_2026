---
id: TST-07
name: test_schema_sync.py — @schema_sync — Skill Outcome: All 4 Layers Patched
epic: Epic 5 - Tests
status: [x] Done
summary: Skill outcome contract test. Regardless of which skill was used, asserts that YAML contains merged_at, prompts contain no merged=1, and ChromaDB has no stale chunks. The definitive pass/fail for any schema-sync skill.
---

# TST-07 — @schema_sync — Skill Outcome: All 4 Layers Correctly Patched

- Epic: Epic 5 - Tests
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L185)

## Objective

Define the **skill outcome contract**: the assertions that must be true after *any* schema-sync skill (00_naive, 01_structured, 02_agent_assisted, 03_fully_guided) has been applied. A skill passes this test if and only if it correctly patches all four layers.

## Description

This test does not care how the patching was done — it only checks that the final file state matches the expected post-sync state:

**Layer 1 — YAML contract:**
- `agentic_system/schema/github_events.yaml` contains a `merged_at` column entry.
- The `merged_at` column type is `Nullable(DateTime)`.
- No column description contains the string `merged = 1`.

**Layer 2 — NL2SQL prompt:**
- `agentic_system/agents_core/nl2sql/prompts/system.md` does not contain `merged = 1`.
- The file contains `merged_at IS NOT NULL` or `merged_at` references.

**Layer 3 — RAG prompt:**
- `agentic_system/agents_core/rag/prompts/system.md` does not contain `merged = 1`.
- The file contains `merged_at` references.

**Layer 4 — ChromaDB:**
- Mock or integration: no chunk in `schema_docs` or `qa_examples` has `stale: True` metadata.
- No chunk document contains `merged = 1`.

The test is marked `@pytest.mark.schema_sync`. It reads the actual files on disk — not mocks — for layers 1–3. ChromaDB is tested via mock unless an integration flag is set.

## Scope

- `tests/test_schema_sync.py::test_all_four_layers_patched`
- Marked `@pytest.mark.schema_sync`.

## Out Of Scope

- How the patching happened (skill or tool does not matter).
- Testing prompt quality or LLM output.
- The `SchemaSyncReport` structure (tested in TST-09).

## Deliverables

- `tests/test_schema_sync.py` with `test_all_four_layers_patched`.
- Inline `mock_chroma_client_post_sync` fixture returning chunks with `stale: False` and `merged_at IS NOT NULL` content.

## Acceptance Criteria

- YAML file check: `merged_at` column present, no `merged = 1` in any description field.
- NL2SQL prompt check: `merged = 1` absent, `merged_at` present.
- RAG prompt check: `merged = 1` absent, `merged_at` present.
- ChromaDB mock check: no chunk document contains `merged = 1`, all metadata `stale: False`.
- Test can be run without live services (all external calls mocked).

## Dependencies

- AGT-04: `agentic_system/schema/github_events.yaml` (read directly).
- AGT-01/02: prompt files at known paths (read directly).
- DEV-09: `schema_sync.py` is the reference tool — if test fails after running schema_sync, something is broken.
- TST-02: `tests/fixtures/github_events_post_migration.yaml` as the expected YAML state reference.

## Assumptions

- The test runs on a post-sync file state — either the developer used a skill or ran `schema_sync.py` manually.
- The test is not idempotent with file state: it must be run *after* a skill or tool has been applied.
- For CI: fixture files represent the expected post-sync state directly (no live patching in the test itself).

## Verification

```bash
# After running schema_sync or a skill:
uv run pytest tests/test_schema_sync.py::test_all_four_layers_patched -v -m schema_sync
```

Expected:
```
tests/test_schema_sync.py::test_all_four_layers_patched PASSED
```

Failure messages must be specific per layer:
```
AssertionError: Layer 2 (NL2SQL prompt): 'merged = 1' still present in system.md
```

## Notes

- This is the most important test in the suite — it is the contract a skill must satisfy.
- A skill that fixes only 3 layers will fail this test, making the gap visible.
- Designed so any future migration can extend this test by adding new column checks.
