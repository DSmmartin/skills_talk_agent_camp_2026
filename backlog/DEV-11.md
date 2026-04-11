---
id: DEV-11
name: --dry-run Flag for schema_sync.py
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: --dry-run flag that passes through all four patch scripts, shows every change that would be made, and touches nothing. Allows safe inspection of the sync plan before committing.
---

# DEV-11 — --dry-run Flag for schema_sync.py

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P1
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L162)

## Objective

Let the presenter (or a developer) inspect exactly what `schema_sync.py` would change before running a live sync. Especially useful during the demo to show the audience what is about to happen before committing.

## Description

The `--dry-run` flag is accepted by `schema_sync.py` and passed to all four patch functions:
- `yaml_patch.patch(table, live, dry_run=True)` — computes changes but does not write the YAML file.
- `chroma_patch.patch(dry_run=True)` — identifies stale chunks and computes new documents but does not upsert.
- `prompt_patch.patch(dry_run=True)` — applies replacements in memory but does not write prompt files.

The `SchemaSyncReport` is populated with the same change lists as a live run, and its `dry_run` flag is set to `True` so `print()` appends `[DRY RUN]` to the header and `Run without --dry-run to apply.` to the summary.

No rollback state is saved during a dry-run.

## Scope

- `--dry-run` argparse flag in `schema_sync.py`.
- `dry_run` parameter thread-through in all four patch scripts.
- `SchemaSyncReport.dry_run` field and display.

## Out Of Scope

- Partial dry-run (e.g. dry-run ChromaDB but live YAML) — all-or-nothing only.

## Deliverables

- `--dry-run` flag in `dev_tools/schema_sync.py` (implemented as part of DEV-09).
- `dry_run` parameter in `dev_tools/scripts/yaml_patch.py`, `chroma_patch.py`, `prompt_patch.py`.

## Acceptance Criteria

- `schema_sync.py --dry-run` produces the same change list as a live run but writes nothing.
- After `--dry-run`, the YAML file, prompt files, and ChromaDB are unchanged.
- `SchemaSyncReport.print()` shows `[DRY RUN]` in the header.
- `--dry-run` and `--rollback` are mutually exclusive (enforced in argparse).

## Dependencies

- DEV-09: `schema_sync.py` entry point.
- DEV-06, DEV-07, DEV-08: each patch script accepts and honours `dry_run`.

## Assumptions

- `dry_run=True` means no filesystem or database writes of any kind.
- The change lists are computed even in dry-run mode so the report is accurate.

## Verification

```bash
# Make migrate first (to create drift)
make migrate

# Dry run — confirm nothing is written
uv run python dev_tools/schema_sync.py --table github_events --dry-run

# Verify YAML unchanged (should still show drift)
uv run python scripts/validate_schema.py
# Expected: "N drift(s) detected." — NOT "No drift"

# Verify prompts unchanged (should still contain old references)
grep -c "merged = 1" agentic_system/agents_core/nl2sql/prompts/system.md
# Expected: non-zero
```

## Notes

- Completed 2026-04-08 as part of DEV-09 implementation.
- The Makefile provides `make schema-sync-dry` as a convenience alias.
