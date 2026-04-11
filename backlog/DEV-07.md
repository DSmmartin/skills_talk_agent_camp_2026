---
id: DEV-07
name: dev_tools/scripts/yaml_patch.py
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Reads agentic_system/schema/<table>.yaml, diffs it against the live ClickHouse schema, adds missing columns, updates changed types and post-migration descriptions, and writes the patched YAML back. Returns a list of YamlChange records.
---

# DEV-07 — dev_tools/scripts/yaml_patch.py

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L158)

## Objective

Keep the `agentic_system/schema/github_events.yaml` contract in sync with the live ClickHouse schema after a migration. After `make migrate`, the YAML still describes `merged UInt8` while the DB has both `merged UInt8` (zeroed) and `merged_at Nullable(DateTime)`. `yaml_patch.py` closes that gap so `make validate-schema` reports no drift.

## Description

`yaml_patch.patch(table, live_cols, dry_run)` loads the YAML contract, compares it to `live_cols` (a `{name: type}` dict from `clickhouse_introspect.introspect()`), and applies three categories of change:

1. **Type change** — updates `type:` for any column whose live type differs from the YAML.
2. **Description refresh** — updates the human-readable `description:` for columns in `_POST_MIGRATION_DESCRIPTIONS` (currently `merged` and `merged_at`).
3. **New column** — appends a new column entry for any column present in live DB but missing from the YAML.

After patching, sets `schema_state: post_migration_synced` at the document level and writes the file with `yaml.dump`. Returns a list of `YamlChange` records for the `SchemaSyncReport`.

Also exposes `load_yaml(table) → dict` for use by other modules.

## Scope

- `dev_tools/scripts/yaml_patch.py`:
  - `YamlChange` dataclass: `action`, `column`, `detail`
  - `load_yaml(table) → dict`
  - `save_yaml(table, doc)`
  - `patch(table, live_cols, dry_run) → list[YamlChange]`
  - `main()` CLI entry point

## Out Of Scope

- Removing columns that exist in the YAML but not in live DB (kept to preserve historical record).
- Reformatting or reordering the YAML structure beyond the patched fields.

## Deliverables

- `dev_tools/scripts/yaml_patch.py`

## Acceptance Criteria

- After patching, `make validate-schema` reports "No drift" on the post-migration state.
- New `merged_at` column appears in the YAML with the correct type and a post-migration description.
- `merged` column description is updated to note it is zeroed out and not to use `merged = 1`.
- `--dry-run` prints the changes without writing the file.
- Returns empty list (no-op) when the YAML already matches live.

## Dependencies

- AGT-04: `agentic_system/schema/github_events.yaml` exists.
- DEV-05: `introspect()` provides the `live_cols` argument.
- `yaml` (PyYAML): available as a transitive dependency.

## Assumptions

- The YAML file structure follows the `{table:, columns: [{name:, type:, description:}]}` schema established in AGT-04.
- `yaml.dump` with `sort_keys=False` preserves column order.
- Description strings in `_POST_MIGRATION_DESCRIPTIONS` are authoritative for the two migration-sensitive fields.

## Verification

```bash
# Syntax check
uv run python -c "import ast; ast.parse(open('dev_tools/scripts/yaml_patch.py').read()); print('OK')"

# Dry run (after make migrate)
uv run python dev_tools/scripts/yaml_patch.py --dry-run

# Full patch
uv run python dev_tools/scripts/yaml_patch.py

# Confirm validate-schema passes
uv run python scripts/validate_schema.py
```

Expected after full patch:
```
── Drift Report
  No drift — live schema matches YAML contract exactly.
```

## Notes

- Completed 2026-04-08.
- The script intentionally does NOT remove columns that are in the YAML but gone from live DB. In the demo, the `merged` column still exists in ClickHouse (zeroed), so there is nothing to remove.
- `schema_state: post_migration_synced` added to the YAML document root so downstream tools can detect whether a sync has been run.
