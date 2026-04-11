---
id: MIG-06
name: Makefile Targets — make migrate, make rollback, make validate-schema
epic: Epic 3 - Migration Scripts (Act 2)
status: [x] Done
summary: Wire the migration, rollback, and validation scripts into Makefile targets so the presenter runs a single command during the demo.
---

# MIG-06 - Makefile Targets — make migrate, make rollback, make validate-schema

- Epic: Epic 3 - Migration Scripts (Act 2)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L121)

## Objective

Give the presenter one-command access to the Act 2 migration and rollback during the demo.

## Description

The `migrate`, `rollback`, and `validate-schema` targets in `Makefile` delegate to their respective scripts via `uv run`. The targets use `uv run` (not `python3`) to ensure the correct venv and dependencies are used regardless of the shell environment.

## Scope

- Update `migrate` target: `uv run python scripts/migrate_schema.py`.
- Update `rollback` target: `uv run python scripts/rollback_schema.py`.
- Add `validate-schema` target: `uv run python scripts/validate_schema.py`.
- Add `validate-schema` to `.PHONY` and to `make help` output.
- Remove placeholder guards from `migrate` and `rollback` (previously checked whether scripts existed).

## Out Of Scope

- `--dry-run` flag in Makefile (call the scripts directly for that).

## Deliverables

- Updated `Makefile` with three clean targets.

## Acceptance Criteria

- `make migrate` runs the migration and prints the expected summary.
- `make rollback` runs the rollback and prints the expected summary.
- `make validate-schema` exits 0 when clean, 1 when drift detected.
- `make help` lists all three targets with descriptions.
- All targets use `uv run` for environment consistency.

## Dependencies

- MIG-01: `scripts/migrate_schema.py` must exist.
- MIG-03: `scripts/rollback_schema.py` must exist.
- MIG-04: `scripts/validate_schema.py` must exist.

## Verification

```bash
make help | grep -E 'migrate|rollback|validate'
make migrate
make validate-schema; echo "exit $?"
make rollback
make validate-schema && echo "exit 0 — clean"
```

## Notes

- Completed 2026-04-08.
- Previous `migrate` and `rollback` targets had `if [ -f scripts/... ]` guards — removed after scripts were created.
