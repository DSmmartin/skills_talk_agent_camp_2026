---
id: DEV-14
name: End-to-End — Agent Returns Correct Rows After schema_sync
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Verify that after running schema_sync.py following make migrate, the ghost contributor question in the TUI returns correct (non-zero) rows, completing the Act 3 demo loop.
---

# DEV-14 — End-to-End — Agent Returns Correct Rows After schema_sync

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L165)

## Objective

Confirm that the full Act 3 demo loop works end-to-end: after `make migrate` causes silent wrong answers, running `schema_sync.py` patches all four layers, and the same ghost contributor question in the TUI returns correct rows again. This is the Definition-of-Done gate for Epic 4.

## Description

This task is a verification milestone, not a code deliverable. It confirms that DEV-05 through DEV-13 compose correctly and that the patched layers actually fix the agent behaviour:

1. Start from a clean, seeded, pre-migration state with the TUI returning correct rows.
2. Run `make migrate` — confirm the agent returns 0 rows (Act 2 verified).
3. Run `python dev_tools/schema_sync.py --table github_events` — confirm the SchemaSyncReport shows changes in all four layers.
4. Ask the same ghost contributor question in the TUI — confirm non-zero rows are returned.
5. Optionally: run `make validate-schema` — confirm no drift.

The Act 3 demo is complete when step 4 passes.

## Scope

- Verification of the Act 3 end-to-end flow. No new code.
- `PRODUCT_BACKLOG.md` Definition of Done checkboxes for schema_sync updated to `[x]`.

## Out Of Scope

- Automated end-to-end test (that is TST-07/08 in Epic 5).
- Any code changes — if verification fails, the bug is in DEV-06/07/08.

## Deliverables

- Updated `PRODUCT_BACKLOG.md` Definition of Done checkboxes.

## Acceptance Criteria

- After `schema_sync.py`, `make validate-schema` reports "No drift".
- After `schema_sync.py`, `SELECT count() FROM github_events WHERE merged_at IS NOT NULL` returns ~1.6M.
- After `schema_sync.py`, the NL2SQL prompt no longer contains `merged = 1`.
- After `schema_sync.py`, ChromaDB `schema_docs:pr_fields` document does not contain `merged = 1`.
- The TUI ghost contributor question returns non-zero rows.

## Dependencies

- DEV-05 through DEV-13: all patch scripts and schema_sync.py implemented.
- MIG-01: `make migrate` must be working.
- AGT-01 through AGT-10: the agentic system must be fully functional.

## Assumptions

- Services (ClickHouse, ChromaDB, MLflow) are running via `make up`.
- A valid OpenAI or Azure OpenAI key is in `.env`.
- The same dataset query used in Act 1 verification is used here.

## Verification

Full Act 3 verification procedure:

```bash
# 0. Clean state
make rollback
make seed-vectors

# 1. Act 1 baseline — confirm correct rows
uv run python agentic_system/main.py
# Ask: "Show me repositories where users opened PRs but never got one merged"
# Confirm: non-zero rows returned

# 2. Act 2 — break
make migrate
# Ask same question in TUI → expect 0 rows, no error

# 3. Act 3 — fix
uv run python dev_tools/schema_sync.py --table github_events
# Confirm SchemaSyncReport shows changes in YAML, ChromaDB, and prompts

# 4. Validate schema
uv run python scripts/validate_schema.py
# Expected: "No drift — live schema matches YAML contract exactly."

# 5. Confirm agent healed
# Ask same question in TUI → expect non-zero rows
```

Expected SchemaSyncReport (step 3):
```
  YAML contract  (2 change(s))
    • yaml:added:merged_at ...
    • yaml:updated:merged ...

  ChromaDB chunks  (3 chunk(s) patched)
    • chroma:patched:schema_docs:pr_fields ...
    • chroma:patched:qa_examples:ghost_contribs ...
    • chroma:patched:qa_examples:unmerged_prs ...

  Agent prompts  (2 file(s) patched)
    • prompt:patched:...nl2sql/prompts/system.md ...
    • prompt:patched:...rag/prompts/system.md ...

  Total: 7 change(s) across YAML contract, ChromaDB chunks, Agent prompts.
```

## Notes

- Completed 2026-04-08.
- PRODUCT_BACKLOG.md Definition of Done checkboxes for `schema_sync` and "agent returns correct rows" updated to `[x]`.
- The Act 3 loop is the narrative centrepiece of the demo: one command fixes everything that four-layer migration broke.
