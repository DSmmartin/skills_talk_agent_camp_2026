---
id: DEV-12
name: --rollback Flag for schema_sync.py
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: --rollback flag that reverses a previous schema_sync run by restoring the YAML contract and prompt files from saved snapshots. ChromaDB rollback requires re-seeding via make seed-vectors.
---

# DEV-12 — --rollback Flag for schema_sync.py

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P2
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L163)

## Objective

Allow a developer to undo a `schema_sync` run and restore the system to its pre-sync state. Useful when the demo is reset between runs (`make rollback` + `make seed-vectors`) and the presenter needs to bring the prompts and YAML back to the pre-migration state too.

## Description

Before making any changes, `schema_sync.sync()` captures snapshots of the YAML contract and all prompt file contents and stores them in `dev_tools/.schema_sync_rollback.json` (only written on a live, non-dry-run sync that makes at least one change).

`--rollback` reads that file and:
1. Writes the saved YAML doc back to `agentic_system/schema/github_events.yaml`.
2. Writes each saved prompt file content back to its original path.
3. Prints a note that ChromaDB requires `make seed-vectors` to restore (re-seeding from the source `.txt` files is the ground truth for pre-migration chunk content).

`--rollback` and `--dry-run` are mutually exclusive.

## Scope

- `--rollback` argparse flag in `schema_sync.py`.
- `_save_rollback_state(table, state)` — writes `.schema_sync_rollback.json`.
- `_load_rollback_state()` — reads it; raises `FileNotFoundError` if not present.
- `_do_rollback(table)` — restores YAML and prompt files from the snapshot.

## Out Of Scope

- ChromaDB rollback via this flag (use `make seed-vectors`).
- Multiple rollback levels (only the most recent sync is reversible).

## Deliverables

- `--rollback` flag in `dev_tools/schema_sync.py`.
- `.schema_sync_rollback.json` created in `dev_tools/` after a live sync.

## Acceptance Criteria

- After a live sync + `--rollback`, the YAML file and prompt files are restored to pre-sync content.
- `--rollback` with no prior sync exits with a clear error: "No rollback state found."
- `--rollback --dry-run` is rejected with a usage error.
- `.schema_sync_rollback.json` is listed in `.gitignore`.

## Dependencies

- DEV-09: `schema_sync.py` saves the rollback state as part of `sync()`.
- DEV-07: YAML file path used for restore.
- DEV-08: `PROMPT_FILES` list used for restore.

## Assumptions

- Only the last sync is reversible — there is no rollback stack.
- ChromaDB content cannot be trivially snapshotted in the rollback file (chunks can be large); `make seed-vectors` is the documented restore path.

## Verification

```bash
# 1. Start from clean state
make rollback   # restore ClickHouse
make seed-vectors  # restore ChromaDB

# 2. Migrate + sync
make migrate
uv run python dev_tools/schema_sync.py --table github_events

# 3. Confirm sync was applied
grep "merged_at" agentic_system/agents_core/nl2sql/prompts/system.md | head -2

# 4. Rollback
uv run python dev_tools/schema_sync.py --table github_events --rollback

# 5. Confirm restored
grep "merged = 1" agentic_system/agents_core/nl2sql/prompts/system.md | head -2
# Expected: lines with 'merged = 1' are back

uv run python scripts/validate_schema.py
# Expected: drift detected (YAML restored to pre-sync state)

# 6. No rollback state test
rm -f dev_tools/.schema_sync_rollback.json
uv run python dev_tools/schema_sync.py --rollback
# Expected: ERROR: No rollback state found...
```

## Notes

- Completed 2026-04-08 as part of DEV-09 implementation.
- `.schema_sync_rollback.json` should be added to `.gitignore` (it is a local runtime artefact).
- The rollback for ChromaDB is intentionally delegated to `make seed-vectors` because the canonical pre-migration chunk content lives in `db/vectordb/collections/`.
