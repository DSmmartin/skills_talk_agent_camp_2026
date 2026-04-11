---
id: IMP-02
name: make seed LOCAL=1 Makefile Parameter
epic: Epic 8 - Improvements
status: [x] Done
summary: Add LOCAL parameter to make seed so presenters can load the controlled 10–20 row dataset instead of pulling from GitHub Archive.
---

# IMP-02 - make seed LOCAL=1 Makefile Parameter

- Epic: Epic 8 - Improvements
- Priority: P1
- Estimate: S
- Status: [x] Done
- Source: PRODUCT_BACKLOG.md

## Objective

Update the `seed` Makefile target so that `make seed LOCAL=1` truncates `github_events` and loads rows from `db/clickhouse/init/03_seed_local.sql`, while `make seed` (no parameter) retains the current GitHub Archive pull behavior exactly as-is.

## Description

Workshop presenters need a single-command fallback when the GitHub Archive S3 source is slow or unavailable. Passing `LOCAL=1` to `make seed` should transparently switch to the local dummy dataset created in IMP-01 — no changes to scripts, no new dependencies, no extra steps.

The implementation copies `03_seed_local.sql` into the running ClickHouse container and executes it via `clickhouse-client --multiquery`. The existing `02_seed_data.sh` path must remain completely unchanged.

## Scope

- Add `LOCAL ?= 0` variable declaration to the Makefile.
- Update the `seed` target to branch on `$(LOCAL)`:
  - `LOCAL=0` (default): current `docker compose exec ... 02_seed_data.sh` call, unchanged.
  - `LOCAL=1`: copy `db/clickhouse/init/03_seed_local.sql` into the container and execute it via `clickhouse-client --multiquery`.
- Update the `help` target to document `make seed LOCAL=1`.
- Update `.PHONY` if any helper targets are added.

## Out Of Scope

- Modifying `02_seed_data.sh`.
- Creating `03_seed_local.sql` (covered by IMP-01).
- Adding any new Python scripts or Docker images.
- Changing the `seed-vectors` target or any other Makefile target.
- Parameterising row counts or repo names at `make seed LOCAL=1` invocation time.

## Deliverables

- Updated `Makefile` with `LOCAL` parameter support on the `seed` target and updated `help` text.

## Acceptance Criteria

- `make seed` (no flag) behaves exactly as before — invokes `02_seed_data.sh` inside the container.
- `make seed LOCAL=1` truncates `github_events` and loads rows from `03_seed_local.sql` with no internet access required.
- `make help` output mentions `LOCAL=1` as an option for `make seed`.
- No changes are made to `02_seed_data.sh` or any other existing script.

## Dependencies

- `IMP-01` must be completed so `db/clickhouse/init/03_seed_local.sql` exists before this target is used.

## Assumptions

- The ClickHouse container is already running when `make seed LOCAL=1` is invoked (same assumption as the current `make seed`).
- `docker compose cp` or a bind-mount approach is acceptable for getting the SQL file into the container.
- No new Makefile variables beyond `LOCAL` are needed.

## Verification

1. Run `make seed` and confirm it still pulls from GitHub Archive (or smoke-test with `GITHUB_ARCHIVE_TARGET_ROWS=10`).
2. Run `make seed LOCAL=1` with the container up and confirm:
   - `github_events` is truncated before load.
   - Row count after load matches the number of INSERTs in `03_seed_local.sql`.
3. Run `make help` and confirm `LOCAL=1` appears in the `seed` description.

## Notes

- Created 2026-04-09 as the second task of Epic 8 - Improvements.
- Depends on IMP-01 for the SQL file, but the Makefile change itself can be drafted before IMP-01 is complete.
