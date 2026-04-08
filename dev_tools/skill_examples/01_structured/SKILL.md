---
name: schema-sync-structured
description: Fix an agentic NL2SQL system after a database schema change. Inspect the schema contract, agent prompts, and vector database chunks for stale field references and update them.
---

# Schema Sync — Structured

After a database schema migration, the following files and systems may contain stale field references.

## Files to inspect

- `agentic_system/schema/github_events.yaml` — machine-readable schema contract
- `agentic_system/agents_core/nl2sql/prompts/system.md` — NL2SQL agent system prompt
- `agentic_system/agents_core/rag/prompts/system.md` — RAG agent system prompt
- ChromaDB collections: `schema_docs`, `qa_examples` — vector RAG chunks

## What to look for

1. Read the live ClickHouse schema: `SELECT name, type FROM system.columns WHERE table = 'github_events' ORDER BY position`
2. Find references to old field names and SQL predicates in the files above.
3. Update each file to use the new field names, types, and predicate syntax.
4. For ChromaDB: find chunks with `stale: True` in their metadata and update their content.

## Validation

Run `python scripts/validate_schema.py` to check whether the YAML contract matches the live schema.
