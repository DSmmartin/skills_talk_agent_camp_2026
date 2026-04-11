---
id: MIG-02
name: Migration Marks ChromaDB Chunks Stale — Content Intentionally Left Wrong
epic: Epic 3 - Migration Scripts (Act 2)
status: [x] Done
summary: After the ClickHouse migration, mark migration-sensitive ChromaDB chunks as stale without fixing their content — leaving the RAG layer broken for Act 2.
---

# MIG-02 - Migration Marks ChromaDB Chunks Stale — Content Intentionally Left Wrong

- Epic: Epic 3 - Migration Scripts (Act 2)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L117)

## Objective

After the ClickHouse column rename, mark all ChromaDB chunks that reference the old schema as stale — but do not update their text content. The RAG layer then returns outdated field names, contributing to Act 2's four-layer cascade failure.

## Description

ChromaDB chunks seeded with `migration_sensitive: True` reference the old `merged UInt8` field in their text. After migration, these chunks are incorrect but still returned by semantic search. This task marks them with `stale: True` and `schema_state: post_migration_stale` in their metadata. The content is deliberately NOT changed — schema-sync in Act 3 is responsible for re-embedding corrected content.

This task is implemented inside `scripts/migrate_schema.py` (MIG-01), not as a separate file.

## Scope

- For every ChromaDB chunk where `migration_sensitive: True`, update metadata: add `stale: True`, set `schema_state: post_migration_stale`.
- Do not modify document text (the wrong field names must persist for Act 2).
- Covered by `--dry-run` flag in `migrate_schema.py`.

## Out Of Scope

- Fixing chunk content (that is schema-sync, Epic 4, DEV-06).
- Chunks without `migration_sensitive: True` are not touched.

## Deliverables

- ChromaDB metadata update logic inside `scripts/migrate_schema.py`.

## Acceptance Criteria

- After `make migrate`, all chunks with `migration_sensitive: True` have `stale: True` and `schema_state: post_migration_stale`.
- Document text of affected chunks is unchanged (still references `merged = 1`).
- Chunks without `migration_sensitive: True` are unaffected.

## Dependencies

- MIG-01: ClickHouse migration must run first (same script).
- INF-04, INF-05: ChromaDB running and seeded with `migration_sensitive` metadata.

## Notes

- Completed 2026-04-08 as part of MIG-01 (`scripts/migrate_schema.py`).
- Three chunks affected: `qa_examples:ghost_contribs`, `qa_examples:unmerged_prs`, `schema_docs:pr_fields`.
- The stale flag is the signal that schema-sync uses in Act 3 to identify which chunks need re-embedding.
