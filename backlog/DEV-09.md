---
id: DEV-09
name: dev_tools/schema_sync.py — Full CLI Composing All Patch Scripts
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Main CLI that orchestrates clickhouse_introspect → yaml_patch → chroma_patch → prompt_patch in one pass. Saves a rollback snapshot, prints a SchemaSyncReport, and supports --dry-run and --rollback flags.
---

# DEV-09 — dev_tools/schema_sync.py — Full CLI Composing All Patch Scripts

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L160)

## Objective

Give the Act 3 presenter a single command that patches all four broken layers after `make migrate` and prints a complete change log. This is the payoff of Epic 4 — one command restores the agent from silent wrong answers to correct rows.

## Description

`schema_sync.py` is the Act 3 developer tool. It composes the four patch scripts in sequence:

1. **Step 1 — ClickHouse introspect** (`clickhouse_introspect.introspect()`) — reads the live schema and prints all columns.
2. **Step 2 — YAML patch** (`yaml_patch.patch()`) — updates `agentic_system/schema/github_events.yaml`.
3. **Step 3 — ChromaDB patch** (`chroma_patch.patch()`) — fixes stale chunks and re-embeds.
4. **Step 4 — Prompt patch** (`prompt_patch.patch()`) — fixes NL2SQL and RAG system prompts.

Before patching, it captures snapshots of the YAML contract and prompt files for rollback. After patching, it saves the snapshots to `dev_tools/.schema_sync_rollback.json` and prints a `SchemaSyncReport`.

Flags:
- `--dry-run` — computes all changes but writes nothing; report shows `[DRY RUN]`.
- `--rollback` — restores YAML and prompts from the saved snapshot (ChromaDB via `make seed-vectors`).

## Scope

- `dev_tools/schema_sync.py`:
  - `sync(table, dry_run) → SchemaSyncReport` — importable core function
  - `_save_rollback_state(table, state)` / `_load_rollback_state()` — snapshot persistence
  - `_do_rollback(table)` — restores YAML and prompts from snapshot
  - `main()` — argparse CLI entry point

## Out Of Scope

- ClickHouse schema mutations (that is `scripts/migrate_schema.py`).
- ChromaDB rollback via this command (use `make seed-vectors`).

## Deliverables

- `dev_tools/schema_sync.py`
- `make schema-sync` and `make schema-sync-dry` Makefile targets (DEV-06b)

## Acceptance Criteria

- Running `schema_sync.py` after `make migrate` patches all four layers and prints the SchemaSyncReport.
- `make validate-schema` reports "No drift" after a successful sync.
- `--dry-run` writes nothing; the report accurately shows what would change.
- `--rollback` restores YAML and prompts to pre-sync content.
- `--dry-run` and `--rollback` are mutually exclusive (exits with error if both given).
- Running on an already-synced system is a no-op (empty change lists, no file writes).

## Dependencies

- DEV-05: `clickhouse_introspect.introspect()`.
- DEV-06: `chroma_patch.patch()`.
- DEV-07: `yaml_patch.patch()` and `yaml_patch.load_yaml()`.
- DEV-08: `prompt_patch.patch()` and `prompt_patch.PROMPT_FILES`.
- DEV-10: `SchemaSyncReport` dataclass.
- DEV-11: `--dry-run` flag (implemented here).
- DEV-12: `--rollback` flag (implemented here).

## Assumptions

- Services (ClickHouse, ChromaDB) are running when the sync is executed.
- `dev_tools/.schema_sync_rollback.json` is not committed to git (runtime artefact).

## Verification

```bash
# Syntax check
uv run python -c "import ast; ast.parse(open('dev_tools/schema_sync.py').read()); print('OK')"

# Import check
uv run python -c "from dev_tools.schema_sync import sync; print('OK')"

# Dry run (after make migrate, services up)
uv run python dev_tools/schema_sync.py --table github_events --dry-run

# Full sync
uv run python dev_tools/schema_sync.py --table github_events

# Confirm no drift
uv run python scripts/validate_schema.py
```

Expected final output:
```
════════════════════════════════════════════════════════════
  Schema Sync Report — github_events
  YYYY-MM-DD HH:MM:SS UTC
════════════════════════════════════════════════════════════
  YAML contract  (2 change(s))  ...
  ChromaDB chunks  (3 chunk(s) patched)  ...
  Agent prompts  (2 file(s) patched)  ...
  Total: 7 change(s) across YAML contract, ChromaDB chunks, Agent prompts.
════════════════════════════════════════════════════════════
```

## Notes

- Completed 2026-04-08.
- `sync()` is importable so `03_fully_guided/patch.py` and tests can call it directly.
- The rollback snapshot excludes ChromaDB content by design; `make seed-vectors` is documented as the ChromaDB restore path.
- This is the Act 3 centrepiece command: `make schema-sync` is what the presenter types.
