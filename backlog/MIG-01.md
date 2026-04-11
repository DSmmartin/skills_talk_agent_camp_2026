---
id: MIG-01
name: scripts/migrate_schema.py — Rename merged → merged_at
epic: Epic 3 - Migration Scripts (Act 2)
status: [x] Done
summary: Implement the Act 2 schema migration that adds merged_at and zeros out merged, causing the agent to return silent wrong answers.
---

# MIG-01 - scripts/migrate_schema.py — Rename merged → merged_at

- Epic: Epic 3 - Migration Scripts (Act 2)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L116)

## Objective

Implement the Act 2 schema migration so the presenter can trigger the breaking event with `make migrate` during the demo.

## Description

The migration adds a new `merged_at Nullable(DateTime)` column, populates it from the existing `merged UInt8` column, then zeros out `merged` (sets all values to 0). The agent's prompts and RAG still say "use `merged = 1`" — those run without error but return 0 rows. That is the intended silent failure for Act 2.

**Key design decision — zero out, do not drop:** An earlier approach dropped the `merged` column. ClickHouse then threw `UNKNOWN_IDENTIFIER` when the old SQL ran — a noisy error that makes the root cause obvious. Zeroing the column leaves it intact so `merged = 1` executes silently and returns 0 rows. The failure is invisible at the surface, which is the Act 2 demo effect.

MIG-02 (marking ChromaDB chunks stale) is part of this script.

## Scope

- Create `scripts/migrate_schema.py`.
- ClickHouse: ADD COLUMN merged_at, UPDATE merged_at from merged, UPDATE merged = 0.
- All mutations use `SETTINGS mutations_sync = 1` (synchronous — wait before proceeding).
- ChromaDB: for every chunk with `migration_sensitive: True`, update metadata to `stale: True, schema_state: post_migration_stale`. Content left wrong intentionally.
- Support `--dry-run` flag (prints what would happen, touches nothing).
- Guard against running on already-migrated schema (exits with error if `merged_at` already exists).

## Out Of Scope

- Fixing agent prompts or RAG content (that is schema-sync, Epic 4).
- Rollback logic (MIG-03).

## Deliverables

- `scripts/migrate_schema.py` — migration script with `--dry-run` support.

## Acceptance Criteria

- `python scripts/migrate_schema.py --dry-run` prints all planned steps without touching anything.
- `python scripts/migrate_schema.py` completes without error on clean pre-migration state.
- Post-migration: `SELECT count() FROM github_events WHERE merged = 1` returns 0.
- Post-migration: `SELECT count() FROM github_events WHERE merged_at IS NOT NULL` returns ~1.6M.
- Post-migration: ChromaDB chunks with `migration_sensitive: True` have `stale: True` in metadata.
- Running the script a second time exits with a clear error message (already migrated).

## Dependencies

- INF-01, INF-02: ClickHouse running with github_events table.
- INF-04, INF-05: ChromaDB running with seeded chunks.
- AGT-04: `agentic_system/schema/github_events.yaml` exists as the pre-migration contract.

## Assumptions

- ClickHouse MergeTree mutations with `mutations_sync = 1` complete before the next ALTER is issued.
- ChromaDB chunks are identified by `migration_sensitive: True` metadata field (set during seeding in INF-05).

## Verification

```bash
# Dry run
uv run python scripts/migrate_schema.py --dry-run

# Real migration
uv run python scripts/migrate_schema.py

# Confirm silent failure
uv run python -c "
import clickhouse_connect
c = clickhouse_connect.get_client(host='localhost', port=8123)
r1 = c.query('SELECT count() FROM github_events WHERE merged = 1')
r2 = c.query('SELECT count() FROM github_events WHERE merged_at IS NOT NULL')
print('merged=1:', r1.result_rows[0][0])       # expect 0
print('merged_at IS NOT NULL:', r2.result_rows[0][0])  # expect ~1610448
"

# Confirm stale metadata
uv run python -c "
import chromadb
c = chromadb.HttpClient(host='localhost', port=8000)
for col in c.list_collections():
    items = col.get(include=['metadatas'])
    for i, m in enumerate(items['metadatas']):
        if m.get('migration_sensitive'):
            print(items['ids'][i], m.get('schema_state'), m.get('stale'))
"
```

Expected (verified 2026-04-08):
```
merged=1: 0
merged_at IS NOT NULL: 1610448
qa_examples:ghost_contribs post_migration_stale True
qa_examples:unmerged_prs post_migration_stale True
schema_docs:pr_fields post_migration_stale True
```

## Notes

- Completed 2026-04-08.
- Uses stdlib `urllib.request` for ChromaDB HTTP calls (same pattern as `db/vectordb/init/seed_vectors.py`).
- Uses `clickhouse_connect` for ClickHouse (available in project venv).
- MIG-02 (mark ChromaDB stale) is implemented inside this script, not as a separate file.
