---
id: TST-02
name: tests/fixtures/ — Pre/Post Schema YAMLs + Sample Row JSON
epic: Epic 5 - Tests
status: [x] Done
summary: Static fixture files — pre-migration and post-migration github_events.yaml snapshots plus a sample row JSON — used by schema_sync unit tests to validate patching logic without live services.
---

# TST-02 — tests/fixtures/ — Pre/Post Schema YAMLs + Sample Row JSON

- Epic: Epic 5 - Tests
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L179)

## Objective

Provide static snapshot files that represent the YAML contract and a representative DB row at each stage of the migration lifecycle. These files decouple schema_sync unit tests from live services and ensure deterministic test behaviour.

## Description

Three files are needed:

**`tests/fixtures/github_events_pre_migration.yaml`** — a copy of `agentic_system/schema/github_events.yaml` as it exists before `make migrate`. Must contain a `merged` column entry of type `UInt8`.

**`tests/fixtures/github_events_post_migration.yaml`** — the expected YAML state after `schema_sync` has patched it. Must contain `merged_at` of type `Nullable(DateTime)` and retain `merged UInt8` (zeroed-out column still in DB).

**`tests/fixtures/sample_row_pre_migration.json`** — a single representative `github_events` row in the pre-migration schema, as returned by `run_sql_core`. Used by agent tests to verify field presence.

## Scope

- `tests/fixtures/github_events_pre_migration.yaml`
- `tests/fixtures/github_events_post_migration.yaml`
- `tests/fixtures/sample_row_pre_migration.json`

## Out Of Scope

- Post-sync ChromaDB chunk fixtures (patched chunks are validated by reading actual ChromaDB in TST-07 or via mock checks).
- Prompt file snapshots (prompts are read directly in TST-10).

## Deliverables

- `tests/fixtures/` directory with all three files.

## Acceptance Criteria

- `github_events_pre_migration.yaml` is valid YAML and contains a `merged` column.
- `github_events_post_migration.yaml` is valid YAML, contains `merged_at`, and does NOT contain `merged = 1` in any description.
- `sample_row_pre_migration.json` is valid JSON and contains the `merged` field (not `merged_at`).

## Dependencies

- AGT-04: `agentic_system/schema/github_events.yaml` is the source for the pre-migration fixture.
- MIG-01: The post-migration YAML is derived from the expected output of `yaml_patch.py`.

## Assumptions

- Fixtures are static files — they do not query any live service.
- The YAML format matches `agentic_system/schema/github_events.yaml` exactly (same keys, same structure).

## Verification

```bash
# YAML validity
uv run python -c "
import yaml, json, pathlib
pre = yaml.safe_load(pathlib.Path('tests/fixtures/github_events_pre_migration.yaml').read_text())
post = yaml.safe_load(pathlib.Path('tests/fixtures/github_events_post_migration.yaml').read_text())
row = json.loads(pathlib.Path('tests/fixtures/sample_row_pre_migration.json').read_text())

pre_cols = {c['name'] for c in pre['columns']}
post_cols = {c['name'] for c in post['columns']}

assert 'merged' in pre_cols, 'Pre-migration YAML must contain merged'
assert 'merged_at' in post_cols, 'Post-migration YAML must contain merged_at'
assert 'merged' in row, 'Sample row must contain merged field'
print('All fixture checks passed.')
"
```

## Notes

- These are the static ground-truth snapshots. If the migration changes, update these files first.
- TST-09 imports these fixtures directly to test `yaml_patch.patch()` without live ClickHouse.
