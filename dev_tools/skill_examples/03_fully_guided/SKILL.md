---
name: schema-sync-fully-guided
description: Complete schema drift repair for the Ghost Contributors NL2SQL system. Patches all four layers (YAML contract, ChromaDB RAG chunks, NL2SQL prompt, RAG prompt) using validated tooling. Includes dry-run preview, step-by-step fallback, validation, and rollback.
---

# Schema Sync — Fully Guided

Read `dev_tools/README.md` and `dev_tools/skill_examples/03_fully_guided/references/schema-layers.md`
before starting. They contain field-level detail about what each layer holds and what to change.

---

## One-command fix

If the migration matches the standard `merged → merged_at` rename pattern, the full procedure
is automated:

```bash
# Preview what will change (nothing is written)
uv run python dev_tools/schema_sync.py --table github_events --dry-run

# Apply all four patches
uv run python dev_tools/schema_sync.py --table github_events

# Confirm no drift
uv run python scripts/validate_schema.py
```

A `SchemaSyncReport` is printed listing every change made across all four layers.

---

## Step-by-step procedure (for non-standard migrations)

Use this when the one-command fix does not cover the migration, or when you need to apply
patches selectively.

### Pre-check — confirm drift exists

```bash
uv run python scripts/validate_schema.py
```

If "No drift" is reported, the system is already in sync. Stop here.

### Step 1 — Introspect live ClickHouse schema

```bash
uv run python dev_tools/scripts/clickhouse_introspect.py --table github_events
```

Note every column that is new, removed, or type-changed compared to the YAML contract.
See `references/schema-layers.md` for the expected post-migration schema.

### Step 2 — Patch YAML contract

```bash
# Preview
uv run python dev_tools/scripts/yaml_patch.py --table github_events --dry-run

# Apply
uv run python dev_tools/scripts/yaml_patch.py --table github_events
```

If patching manually: edit `agentic_system/schema/github_events.yaml`.
- Add the new column entry (name, type, description).
- Update the description of any renamed or type-changed column to document post-migration semantics.
- Do NOT remove columns that still exist in the DB (even if zeroed out).

### Step 3 — Patch ChromaDB RAG chunks

```bash
# Preview
uv run python dev_tools/scripts/chroma_patch.py --dry-run

# Apply
uv run python dev_tools/scripts/chroma_patch.py
```

If patching manually: use the ChromaDB HTTP API.
- `GET /api/v2/tenants/default_tenant/databases/default_database/collections` — list collections.
- For each collection, `POST .../get` with `{"include": ["documents", "metadatas"]}`.
- For items where `metadata.stale == True`, apply text replacements to the document.
- Re-embed with the 64-dimension deterministic hash (see `references/schema-layers.md#embedding`).
- `POST .../upsert` with updated ids, documents, embeddings, and metadatas.

### Step 4 — Patch agent prompts

```bash
# Preview
uv run python dev_tools/scripts/prompt_patch.py --dry-run

# Apply
uv run python dev_tools/scripts/prompt_patch.py
```

If patching manually: edit the two system prompt files.
- `agentic_system/agents_core/nl2sql/prompts/system.md`
- `agentic_system/agents_core/rag/prompts/system.md`

Replace every occurrence of:
- Old field name → new field name (in the schema table, type annotations, prose)
- Old SQL predicate → new predicate (e.g. `merged = 1` → `merged_at IS NOT NULL`)
- State labels (`pre-migration` → `post-migration`)

See `references/schema-layers.md#prompt-replacements` for the complete replacement list.

### Post-check — confirm drift resolved

```bash
uv run python scripts/validate_schema.py
# Expected: No drift — live schema matches YAML contract exactly.

# Confirm prompts no longer reference old predicate
grep -r "merged = 1" agentic_system/agents_core/
# Expected: no output
```

---

## Rollback

```bash
# Restore YAML and prompts from the pre-sync snapshot
uv run python dev_tools/schema_sync.py --table github_events --rollback

# Restore ChromaDB chunks from source files
make seed-vectors
```

The rollback snapshot is saved to `dev_tools/.schema_sync_rollback.json` by the one-command fix.
If you used step-by-step patching, save file snapshots before making changes.

---

## References

- [`references/schema-layers.md`](references/schema-layers.md) — field mapping, embedding algorithm, prompt replacement list
- [`dev_tools/README.md`](../../README.md) — full file map and quick-start
- [`scripts/validate_schema.py`](../../../scripts/validate_schema.py) — drift detection tool
