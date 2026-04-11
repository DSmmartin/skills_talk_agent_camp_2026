---
id: MIG-03
name: scripts/rollback_schema.py — Full Schema Rollback
epic: Epic 3 - Migration Scripts (Act 2)
status: [x] Done
summary: Implement the rollback script that restores the pre-migration schema in ClickHouse and clears stale metadata in ChromaDB.
---

# MIG-03 - scripts/rollback_schema.py — Full Schema Rollback

- Epic: Epic 3 - Migration Scripts (Act 2)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L118)

## Objective

Allow the presenter to reset to the clean pre-migration state at any point during or after the demo with `make rollback`.

## Description

The rollback restores `merged UInt8` values from `merged_at` and drops the `merged_at` column. ChromaDB chunks are restored to `schema_state: pre_migration` (stale flag removed). After rollback, the agent works correctly again — Act 1 demo path is restored.

The post-migration state has both `merged` (all zeros) and `merged_at` (populated). Rollback re-derives the `merged` values from `merged_at` before dropping it.

## Scope

- Create `scripts/rollback_schema.py`.
- ClickHouse: UPDATE merged = if(isNotNull(merged_at), 1, 0), then DROP COLUMN merged_at.
- ChromaDB: for every chunk with `stale: True`, remove the stale flag and set `schema_state: pre_migration`.
- Support `--dry-run` flag.
- Guard: if already at pre-migration state (merged exists, merged_at absent), exit cleanly.

## Out Of Scope

- Restoring ChromaDB document content (content was never changed — only metadata).
- Resetting agent prompts (prompts are unchanged by migrate; only schema-sync touches them).

## Deliverables

- `scripts/rollback_schema.py` — rollback script with `--dry-run` support.

## Acceptance Criteria

- `python scripts/rollback_schema.py --dry-run` prints all planned steps without touching anything.
- `python scripts/rollback_schema.py` completes without error after migration.
- Post-rollback: `SELECT countIf(merged = 1) FROM github_events WHERE event_type = 'PullRequestEvent'` returns ~1.6M.
- Post-rollback: `merged_at` column is absent from `system.columns`.
- Post-rollback: ChromaDB chunks have `schema_state: pre_migration` and no `stale` key.
- Running on already-rolled-back schema prints "Already at pre-migration state" and exits 0.

## Dependencies

- MIG-01: Migration must have been run (rollback reverses it).

## Assumptions

- `merged_at` is populated correctly from MIG-01 — rollback relies on it to re-derive `merged` values.
- ChromaDB stale flag is the sole signal used to identify chunks to restore.

## Verification

```bash
# After make migrate:
uv run python scripts/rollback_schema.py --dry-run
uv run python scripts/rollback_schema.py

# Verify restored state
uv run python -c "
import clickhouse_connect
c = clickhouse_connect.get_client(host='localhost', port=8123)
cols = {r[0] for r in c.query('SELECT name FROM system.columns WHERE table=\'github_events\'').result_rows}
print('merged present:', 'merged' in cols)
print('merged_at absent:', 'merged_at' not in cols)
r = c.query('SELECT countIf(merged=1) FROM github_events WHERE event_type=\'PullRequestEvent\'')
print('merged=1 count:', r.result_rows[0][0])
"
uv run python scripts/validate_schema.py
```

Expected (verified 2026-04-08):
```
merged present: True
merged_at absent: True
merged=1 count: 1610448
No drift — live schema matches YAML contract exactly.
```

## Notes

- Completed 2026-04-08.
- Uses same HTTP helpers as `migrate_schema.py` for ChromaDB — no chromadb Python client needed.
- Restoring metadata only (no re-embedding) is sufficient because migrate never changed document text.
