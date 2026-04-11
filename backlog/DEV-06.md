---
id: DEV-06
name: dev_tools/scripts/chroma_patch.py
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Finds stale ChromaDB chunks (metadata.stale == True), applies text replacements to update their content for the post-migration schema, re-embeds with the same deterministic hash function, and upserts back. Returns a list of ChromaChange records.
---

# DEV-06 — dev_tools/scripts/chroma_patch.py

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L157)

## Objective

Patch the stale RAG chunks in ChromaDB so the AgentRAG retrieves post-migration schema context. After `make migrate`, chunks are marked `stale: True` by `migrate_schema.py` — their content still references `merged UInt8` and SQL predicates like `merged = 1`. `chroma_patch.py` fixes the text, re-embeds, and upserts.

## Description

The script iterates all ChromaDB collections, finds chunks where `metadata.stale == True`, applies a set of ordered regex replacement rules to each document (e.g. `merged UInt8 → merged_at Nullable(DateTime)`, `merged = 1 → merged_at IS NOT NULL`), re-computes the deterministic hash embedding using the same algorithm as `db/vectordb/init/seed_vectors.py`, and upserts the corrected document + new embedding back into the collection.

Metadata is updated: `stale: False`, `schema_state: post_migration_synced`.

Returns a list of `ChromaChange` dataclass instances (one per patched chunk) for inclusion in the `SchemaSyncReport`.

Supports `--dry-run` flag: scans and reports what would be patched without writing anything.

## Scope

- `dev_tools/scripts/chroma_patch.py`:
  - `patch(dry_run) → list[ChromaChange]` — importable core function
  - `ChromaChange` dataclass: `chunk_id`, `collection`, `replacements_applied`
  - `_apply_text_replacements(text) → (new_text, count)` — regex replacement engine
  - `_embed(text) → list[float]` — deterministic hash embedding (64 dimensions, mirrors `seed_vectors.py`)
  - `main()` CLI entry point

## Out Of Scope

- Deleting or recreating collections.
- Updating the ChromaDB collection-level metadata.
- Re-seeding from source files (use `make seed-vectors` for that).

## Deliverables

- `dev_tools/scripts/chroma_patch.py`

## Acceptance Criteria

- After running `chroma_patch.py` on a post-migration state, no chunks have `stale: True`.
- Patched chunk documents no longer contain `merged = 1` or `merged UInt8`.
- Patched chunk embeddings are recomputed with the same deterministic function used at seed time.
- `--dry-run` prints the chunks that would be patched without modifying ChromaDB.
- Returns empty list (no-op) when no stale chunks exist.

## Dependencies

- INF-04, INF-05: ChromaDB running with seeded collections.
- MIG-01 / MIG-02: `migrate_schema.py` must have run to mark chunks stale.
- `agentic_system/config.py`: `settings.chroma_host`, `settings.chroma_port`.

## Assumptions

- Embedding dimensions are 64 (matches `DEFAULT_DIMENSIONS` in `seed_vectors.py`).
- The same deterministic hash function as seed time ensures query affinity is preserved after patching.
- ChromaDB v2 API: `/api/v2/tenants/{tenant}/databases/{db}/collections/{id}/upsert`.

## Verification

```bash
# Syntax check
uv run python -c "import ast; ast.parse(open('dev_tools/scripts/chroma_patch.py').read()); print('OK')"

# Dry run (after make migrate, services up)
uv run python dev_tools/scripts/chroma_patch.py --dry-run

# Full patch
uv run python dev_tools/scripts/chroma_patch.py

# Confirm no stale chunks remain
uv run python -c "
import chromadb
c = chromadb.HttpClient(host='localhost', port=8000)
for col in c.list_collections():
    items = col.get(include=['metadatas'])
    stale = [m for m in items['metadatas'] if m.get('stale')]
    print(col.name, 'stale:', len(stale))
"
```

Expected after full patch:
```
schema_docs stale: 0
qa_examples stale: 0
```

## Notes

- Completed 2026-04-08.
- Uses stdlib `urllib.request` for HTTP calls (same pattern as `migrate_schema.py` and `seed_vectors.py`).
- The `_embed` function is a copy of `deterministic_embedding` from `seed_vectors.py` — kept local to avoid a circular import from `db/vectordb`.
- Text replacements are ordered: field type annotations first, SQL predicates second, prose descriptions last.
