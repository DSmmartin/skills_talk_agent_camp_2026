---
id: IMP-04
name: Fix Local Seed Reliability — Comments, Pipe, and Mutation State
epic: Epic 8 - Improvements
status: [x] Done
summary: Fix three bugs that silently prevented make seed LOCAL=1 from loading correct data into ClickHouse.
---

# IMP-04 - Fix Local Seed Reliability — Comments, Pipe, and Mutation State

- Epic: Epic 8 - Improvements
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: PRODUCT_BACKLOG.md

## Objective

Resolve three distinct bugs discovered during live verification of `make seed LOCAL=1` that caused the table to load with 0 rows or with all `merged` values forced to 0.

## Description

Three bugs were found and fixed during end-to-end testing of the local seed workflow:

**Bug 1 — Inline SQL comments inside VALUES block.**
ClickHouse rejects `-- comment` lines that appear between rows inside a single `INSERT INTO ... VALUES (...)` statement. The original `03_seed_local.sql` had comments like `-- org/repo-alpha ---` separating groups of rows inside the VALUES block, causing a parse error on execution.

**Bug 2 — `--queries-file` flag does not exist in ClickHouse client.**
The Makefile used `clickhouse-client --multiquery --queries-file /tmp/03_seed_local.sql`. This flag is not available; execution silently exited with code 27. The fix was to pipe via stdin: `sh -c 'clickhouse-client --multiquery < /tmp/03_seed_local.sql'`, matching the pattern used by `02_seed_data.sh`.

**Bug 3 — ClickHouse ALTER TABLE UPDATE mutations persist after TRUNCATE.**
When `make migrate` had previously been run, the mutation `UPDATE merged = 0 WHERE 1` was recorded at table level in ClickHouse. After `TRUNCATE TABLE`, newly inserted rows also had this mutation applied, causing all `merged` values to be stored as 0 — including `alice`, `bob`, `carol`, and `dave` who should have `merged = 1`. The fix was to change `TRUNCATE TABLE` to `DROP TABLE IF EXISTS` + `CREATE TABLE` in `03_seed_local.sql`, which clears all mutation history for the table.

## Scope

- Remove all inline comments from inside the `INSERT INTO ... VALUES (...)` block in `03_seed_local.sql`. Move explanatory comments to the header section above the statement.
- Replace `--queries-file` with stdin pipe in the Makefile `seed` target local branch.
- Replace `TRUNCATE TABLE github_events` with `DROP TABLE IF EXISTS github_events` + `CREATE TABLE github_events (...)` at the top of `03_seed_local.sql`.

## Out Of Scope

- Changing the row content or the set of actors/repos.
- Modifying `02_seed_data.sh` or the default seed path.

## Deliverables

- Updated `db/clickhouse/init/03_seed_local.sql` with header comments only, and DROP+CREATE instead of TRUNCATE.
- Updated `Makefile` local seed branch using stdin pipe.

## Acceptance Criteria

- `make seed LOCAL=1` completes without error on a ClickHouse instance that has previously had `make migrate` run.
- `SELECT count() FROM github_events` returns 18 after the seed.
- `SELECT actor_login, merged FROM github_events WHERE actor_login IN ('alice','bob','carol','dave')` shows `merged = 1` for all closed rows of those actors.
- Ghost contributor query returns exactly 4 rows: `ghost-user-1` through `ghost-user-4`.

## Dependencies

- IMP-01 (the SQL file) and IMP-02 (the Makefile target) must exist before fixes are applied.

## Assumptions

- `docker compose cp` followed by `sh -c 'clickhouse-client --multiquery < ...'` is the correct pattern for feeding a SQL file to the containerised ClickHouse client.
- DROP+CREATE is safe in a workshop context because `make seed LOCAL=1` is always a full reset of the table.

## Verification

Verified by running `make seed LOCAL=1` after `make migrate`, then querying `merged` values directly via `clickhouse_connect` Python client. All 18 rows loaded correctly with `merged = 1` for alice, bob, carol, dave and `merged = 0` for ghost-user-1 through ghost-user-4.

## Notes

- Completed 2026-04-09.
- Bug 3 (mutation persistence) is a subtle ClickHouse behaviour: `ALTER TABLE UPDATE` mutations apply to all new data parts created after the mutation, even after TRUNCATE. DROP+CREATE is the cleanest reset.
