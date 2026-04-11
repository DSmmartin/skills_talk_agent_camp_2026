---
id: DEV-05
name: dev_tools/scripts/clickhouse_introspect.py
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Introspects the live ClickHouse schema for a given table and returns {column: type}. Also provides detect_drift() to diff live vs contract. Used by schema_sync as Step 1.
---

# DEV-05 — dev_tools/scripts/clickhouse_introspect.py

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L156)

## Objective

Provide a reusable, importable function that reads the live ClickHouse schema for any table and returns a `{column_name: type_string}` dict in position order. This is Step 1 of the schema-sync procedure — discover what the DB actually has before deciding what to patch.

## Description

`clickhouse_introspect.introspect(table)` queries `system.columns WHERE table = '<table>' ORDER BY position` and returns an ordered dict. `detect_drift(live, contract)` diffs two such dicts and returns `(added, removed, changed)` tuples — the same diff logic used in `scripts/validate_schema.py` but extracted for reuse across the dev_tools package.

The module also has a standalone `__main__` entry point that prints the schema in a table format.

## Scope

- `dev_tools/scripts/clickhouse_introspect.py`:
  - `introspect(table) → dict[str, str]`
  - `detect_drift(live, contract) → tuple[added, removed, changed]`
  - `main()` CLI entry point

## Out Of Scope

- Writing back to ClickHouse (that is the migration scripts in `scripts/`).
- YAML loading (DEV-07).

## Deliverables

- `dev_tools/scripts/clickhouse_introspect.py`

## Acceptance Criteria

- `introspect("github_events")` returns a non-empty dict when ClickHouse is running.
- `detect_drift(live, contract)` returns the correct `(added, removed, changed)` for the post-migration state.
- CLI prints all columns with their types and a total count.
- Raises `ValueError` if the table is not found.

## Dependencies

- INF-01, INF-02: ClickHouse running with `github_events` table.
- `agentic_system/config.py`: `settings` for connection parameters.
- `clickhouse_connect`: available in project venv.

## Assumptions

- Column position order is stable and matches `system.columns.position`.
- Type strings from ClickHouse are used verbatim (e.g. `Nullable(DateTime)`, `UInt8`).

## Verification

```bash
# Syntax check
uv run python -c "import ast; ast.parse(open('dev_tools/scripts/clickhouse_introspect.py').read()); print('OK')"

# CLI (services must be running)
uv run python dev_tools/scripts/clickhouse_introspect.py --table github_events
```

Expected output (pre-migration):
```
==> ClickHouse Schema: github_events
    localhost:8123/default

  event_type                String
  action                    LowCardinality(String)
  actor_login               String
  repo_name                 String
  created_at                DateTime
  merged                    UInt8
  number                    UInt32
  title                     String

  8 column(s) total
```

Expected output (post-migration):
```
  ...
  merged                    UInt8
  merged_at                 Nullable(DateTime)
  ...
  9 column(s) total
```

## Notes

- Completed 2026-04-08.
- `detect_drift` mirrors the logic in `scripts/validate_schema.py` but is extracted so it can be imported by `03_fully_guided/patch.py` and `schema_sync.py` without importing from `scripts/`.
