---
id: TST-10
name: test_agents.py — Agent Prompt Field Names Pre/Post Sync
epic: Epic 5 - Tests
status: [x] Done
summary: Validates prompt-layer behavior for pre-migration baseline and schema-sync patch output, without requiring live services.
---

# TST-10 — test_agents.py — Agent Prompt Field Names Pre/Post Sync

- Epic: Epic 5 - Tests
- Priority: P1
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L188)

## Objective

Verify that the agent prompt files contain the correct field names at each stage of the demo lifecycle — providing a clear before/after view of what schema_sync changes in the prompt layer.

## Description

`tests/test_agents.py` covers prompt checks for two practical modes:

**Pre-migration mark (`@pytest.mark.pre_migration`):**
- `nl2sql/prompts/system.md` contains `merged` references and pre-migration SQL examples.
- `rag/prompts/system.md` remains in baseline mode (no `merged_at IS NOT NULL` guidance asserted).

**Post-sync mark (`@pytest.mark.schema_sync`):**
- Uses temporary prompt files patched by `prompt_patch.patch()`.
- Asserts patched files contain `merged_at` and no legacy `merged = 1` predicate.

Note: There is no separate post-migration-before-sync test here — that state is implicitly covered by TST-06 (RAG returns stale chunk) and TST-05 (0 rows from SQL).

The pre-migration checks read repo files directly; schema_sync checks validate patch behavior using isolated temporary files so the repo is not mutated by the test.

## Scope

- `tests/test_agents.py` — pre-migration prompt baseline and schema-sync prompt patch behavior.

## Out Of Scope

- Agent behaviour or LLM call mocking (not needed — just checking file content).
- Prompt quality or completeness (beyond field name presence).

## Deliverables

- `tests/test_agents.py` with pre-migration and post-sync prompt assertion tests.

## Acceptance Criteria

- Pre-migration tests pass against the baseline repository state.
- Schema-sync tests pass by patching temporary prompt files and asserting transformed output.
- Each assertion failure message names the file and the missing/unexpected string.

## Dependencies

- AGT-01/02: Prompt files at known paths in `agentic_system/agents_core/`.
- DEV-08: `prompt_patch.py` is what schema_sync uses to update the files checked here.

## Assumptions

- Pre-migration checks target real prompt files on disk.
- Schema-sync checks use temporary files and do not depend on live DB or full repo state transitions.

## Verification

```bash
# Pre-migration (run before make migrate)
uv run pytest tests/test_agents.py -m pre_migration -v

# Schema-sync prompt patch behavior (isolated temp files)
uv run pytest tests/test_agents.py -m schema_sync -v
```

Expected (pre-migration):
```
tests/test_agents.py::test_nl2sql_prompt_contains_pre_migration_field_names PASSED
tests/test_agents.py::test_rag_prompt_baseline_pre_migration PASSED
```

Expected (schema-sync):
```
tests/test_agents.py::test_prompt_field_names_after_sync PASSED
```

## Notes

- These tests double as a regression guard: if anyone manually patches a prompt incorrectly, these tests catch it.
- The pre-migration tests are the "start of demo" baseline; the post-sync tests are the "Act 3 complete" signal.
