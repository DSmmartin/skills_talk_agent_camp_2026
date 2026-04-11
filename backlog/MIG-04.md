---
id: MIG-04
name: scripts/validate_schema.py — Diff Live DB vs YAML Contract
epic: Epic 3 - Migration Scripts (Act 2)
status: [x] Done
summary: Implement a standalone diagnostic that diffs the live ClickHouse schema against the YAML contract and reports drift.
---

# MIG-04 - scripts/validate_schema.py — Diff Live DB vs YAML Contract

- Epic: Epic 3 - Migration Scripts (Act 2)
- Priority: P1
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L119)

## Objective

Give the presenter (and CI) a fast, readable way to see whether the live ClickHouse schema matches `agentic_system/schema/github_events.yaml`. Useful before the demo (confirm clean state) and after migration (confirm drift visible before running schema-sync).

## Description

Reads the YAML contract, queries `system.columns` for the target table, and computes three categories of drift: added (in DB, not in contract), removed (in contract, not in DB), type-changed (both present, different types). Exits 0 when clean, 1 when drift is detected — usable as a CI gate.

## Scope

- Create `scripts/validate_schema.py`.
- Support `--table` flag (default: `github_events`).
- Print: YAML contract columns, live schema columns, drift report with add/remove/type-change categories.
- Exit 0 = no drift; exit 1 = drift detected.

## Out Of Scope

- Fixing any drift (that is schema-sync, Epic 4).
- Checking ChromaDB or prompt state.

## Deliverables

- `scripts/validate_schema.py`.
- `make validate-schema` Makefile target.

## Acceptance Criteria

- Pre-migration: exits 0, prints "No drift — live schema matches YAML contract exactly."
- Post-migration: exits 1, reports `merged` as REMOVED and `merged_at` as ADDED.
- `make validate-schema` runs the script via `uv run`.
- `--table` flag works for any table name.

## Dependencies

- AGT-04: `agentic_system/schema/github_events.yaml` must exist.
- INF-01, INF-02: ClickHouse must be running with the target table.

## Assumptions

- PyYAML is available transitively (via chromadb or mlflow deps).
- Column position is not validated — only name and type matter.

## Verification

```bash
# Pre-migration: expect exit 0
uv run python scripts/validate_schema.py && echo "EXIT 0 — clean"

# Post-migration: expect exit 1
make migrate
uv run python scripts/validate_schema.py; echo "EXIT $?"

# Rollback and re-check
make rollback
uv run python scripts/validate_schema.py && echo "EXIT 0 — clean again"
```

Expected (verified 2026-04-08):
- Pre/post-rollback: exits 0, no drift.
- Post-migration: exits 1, shows `merged` REMOVED and `merged_at` ADDED.

## Notes

- Completed 2026-04-08.
- Exit code 1 on drift is intentional — allows use as `make validate-schema || exit 1` in CI pipelines.
- Schema-sync (Epic 4) will call the same diff logic internally before patching.
