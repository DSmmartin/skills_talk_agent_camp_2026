---
id: TST-12
name: Mocked Complete Flow — pre_migration → post_migration → schema_sync Recovery
epic: Epic 5 - Tests
status: [x] Done
summary: Stateful mocked end-to-end test for the Kubernetes ghost-contributors question proving the full lifecycle: pre works, post-migration silently fails, and fully-guided schema_sync restores correct results.
---

# TST-12 - Mocked Complete Flow — pre_migration → post_migration → schema_sync Recovery

- Epic: Epic 5 - Tests
- Priority: P1
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md)

## Objective

Add a single stateful test that simulates the real demo lifecycle for the specific Kubernetes ghost-contributors question and verifies that recovery only happens after the fully-guided sync path is applied.

## Description

Implemented `tests/test_complete_flow_mocked.py` with a deterministic mocked agent API response and mocked ClickHouse/ChromaDB stores. The test runs four explicit steps:

1. Pre-migration: legacy `merged = 1` SQL returns non-empty rows.
2. Post-migration: same SQL returns 0 rows silently (no exception).
3. Fully-guided fix: run `schema_sync.sync()` (same patch path used by `dev_tools/schema_sync.py`).
4. Post-sync: generated SQL uses `merged_at IS NOT NULL` and returns rows again.

## Scope

- `tests/test_complete_flow_mocked.py`
- `Makefile` target `test-complete-flow`
- `scripts/verify_complete_flow.sh` (live sequence helper)
- `pyproject.toml` marker `complete_flow`

## Out Of Scope

- Live LLM/OpenAI execution in test.
- Full TUI automation.

## Deliverables

- Stateful mocked complete-flow test for `kubernetes/kubernetes`.
- Make target for quick local verification.
- Live verification script with rollback safety trap.

## Acceptance Criteria

- New test fails if recovery is asserted before sync.
- New test passes after schema_sync step in the test flow.
- `make test-complete-flow` passes locally.
- Marker-based suite still passes.

## Dependencies

- TST-07, TST-08, TST-09 (schema_sync contract and utility tests).
- DEV-09 (`dev_tools/schema_sync.py`).

## Assumptions

- Mocked API SQL generation is deterministic and tied to prompt/context state.
- Recovery semantics are validated by predicate transition (`merged = 1` → `merged_at IS NOT NULL`).

## Verification

```bash
# Mocked stateful flow
make test-complete-flow

# Full marker suite including complete-flow
uv run pytest -m "pre_migration or post_migration or schema_sync or complete_flow" --tb=short -q

# Optional live sequence (requires infra up)
make verify-complete-flow
```

Expected verification result:

- Complete-flow test passes.
- Full marker suite passes.
- Live sequence runs migrate -> post checks -> schema_sync -> sync checks -> rollback.

## Notes

- `verify_complete_flow.sh` automatically calls `make rollback` on exit if migration was applied.
