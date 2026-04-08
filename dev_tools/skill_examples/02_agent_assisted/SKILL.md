---
name: schema-sync-agent-assisted
description: Four-layer schema sync procedure for the Ghost Contributors NL2SQL system after a database migration. Covers YAML contract, ChromaDB RAG chunks, NL2SQL prompt, and RAG prompt with a step-by-step repair sequence.
---

# Schema Sync — Agent Assisted

## Context

This system has four layers that break simultaneously when the database schema changes:

| Layer | File / System | What breaks |
|-------|--------------|-------------|
| YAML contract | `agentic_system/schema/github_events.yaml` | Contract no longer matches live DB |
| NL2SQL prompt | `agentic_system/agents_core/nl2sql/prompts/system.md` | Agent generates SQL with old predicates → 0 rows, no error |
| RAG prompt | `agentic_system/agents_core/rag/prompts/system.md` | Agent describes wrong field semantics to the user |
| ChromaDB chunks | `schema_docs`, `qa_examples` collections | RAG retrieves stale context with wrong field names |

## Repair procedure

### Step 1 — Introspect live schema

Query ClickHouse to see what the database actually has:

```sql
SELECT name, type FROM system.columns WHERE table = 'github_events' ORDER BY position
```

Use connection settings from `agentic_system/config.py` (host, port, user, password, database).

### Step 2 — Diff against YAML contract

Load `agentic_system/schema/github_events.yaml` and compare column names and types.
Identify: removed columns, added columns, type changes.

### Step 3 — Patch YAML contract

Update `agentic_system/schema/github_events.yaml`:
- Add entries for new columns with correct type and a clear post-migration description.
- Update the type field for any column whose type changed.
- Update descriptions for migration-sensitive columns (especially merge-related fields).

### Step 4 — Patch agent prompts

In both `system.md` prompt files:
- Replace old field name references with new names.
- Replace old SQL predicates (e.g. `field = 1`) with new equivalents (e.g. `field IS NOT NULL`).
- Update any type annotations in the schema table within the prompt.
- Update state labels (`pre-migration` → `post-migration`).

### Step 5 — Patch ChromaDB chunks

Connect to ChromaDB at `http://localhost:8000` (settings from `agentic_system/config.py`).
For each collection (`schema_docs`, `qa_examples`):
1. Get all items: `POST /api/v2/tenants/default_tenant/databases/default_database/collections/{id}/get` with `{"include": ["documents", "metadatas"]}`
2. Find items where `metadata.stale == True`.
3. Apply the same text replacements to the document content.
4. Re-embed using the deterministic hash function (64 dimensions, same algorithm as `db/vectordb/init/seed_vectors.py`).
5. Upsert back: `POST .../upsert` with updated documents, embeddings, and metadata (`stale: false`, `schema_state: post_migration_synced`).

### Step 6 — Validate

```bash
uv run python scripts/validate_schema.py
```

Expected: `No drift — live schema matches YAML contract exactly.`

Also verify neither prompt file contains the old field predicate syntax.

## Rollback

To restore the pre-sync state: revert the YAML and prompt file changes, then run `make seed-vectors` to restore ChromaDB chunks from source.
