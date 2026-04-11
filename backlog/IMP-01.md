---
id: IMP-01
name: Local Dummy Seed Data for Workshop Fallback
epic: Epic 8 - Improvements
status: [x] Done
summary: Create a controlled local seed file with 10–20 rows across 2–3 repos so workshops can run without network access to GitHub Archive.
---

# IMP-01 - Local Dummy Seed Data for Workshop Fallback

- Epic: Epic 8 - Improvements
- Priority: P1
- Estimate: S
- Status: [x] Done
- Source: PRODUCT_BACKLOG.md

## Objective

Add a static SQL seed file (`db/clickhouse/init/03_seed_local.sql`) that inserts 10–20 handcrafted `PullRequestEvent` rows across 2–3 repo names so the ghost-contributor demo query returns meaningful results without any network access to GitHub Archive.

## Description

The current seeding strategy pulls from `clickhouse-public-datasets.s3.amazonaws.com`, which requires internet access and can be slow or throttled in workshop environments. This task creates a minimal, fully controlled fallback: a plain SQL INSERT file with 10–20 rows that are designed to reproduce the ghost-contributor scenario exactly.

Rows must cover at least two contributor patterns:
- Actors who opened PRs and got at least one merged (`merged = 1`).
- Actors who only opened PRs and never got one merged (`merged = 0` for all their rows) — these are the ghost contributors the demo query surfaces.

The data must use the pre-migration schema (`merged UInt8`, not `merged_at`), so it is also a valid baseline for running Act 2 and Act 3 of the demo.

## Scope

- Create `db/clickhouse/init/03_seed_local.sql` with 10–20 `INSERT INTO github_events` rows.
- Use 2–3 repo names (e.g. `org/repo-alpha`, `org/repo-beta`, `org/repo-gamma`).
- Include actor logins that create the ghost-contributor pattern across those repos.
- Use `event_type = 'PullRequestEvent'`, `action = 'closed'` for merged rows and `action = 'opened'` or `action = 'closed'` with `merged = 0` for ghost rows.
- Keep `created_at` values realistic (e.g. `2024-01-15 10:00:00`).
- Match the pre-migration `github_events` schema exactly: `event_type String`, `action LowCardinality(String)`, `actor_login String`, `repo_name String`, `created_at DateTime`, `merged UInt8`, `number UInt32`, `title String`.

## Out Of Scope

- Modifying `02_seed_data.sh` or the existing GitHub Archive seeding flow.
- Wiring the file into the Makefile (covered by IMP-02).
- Adding post-migration (`merged_at`) rows.
- Creating ChromaDB or MLflow seed data.
- Automated testing of the seed file.

## Deliverables

- `db/clickhouse/init/03_seed_local.sql` with 10–20 INSERT rows covering 2–3 repos and the ghost-contributor pattern.

## Acceptance Criteria

- `db/clickhouse/init/03_seed_local.sql` exists and is valid ClickHouse SQL.
- Running it against a clean `github_events` table (pre-migration schema) inserts the expected rows with no errors.
- `SELECT count() FROM github_events` returns the exact number of rows defined in the file.
- The ghost-contributor query (`actor_login` values that appear only with `merged = 0`) returns at least one result per repo.
- No `merged_at` column references appear in the file.

## Dependencies

- `INF-02` (pre-migration schema) — the INSERT statements must target the column set defined there.

## Assumptions

- 10–20 rows is sufficient to demonstrate the ghost-contributor pattern convincingly in a workshop setting.
- Repo and actor names can be fictional (`org/repo-alpha`, `ghost-user-1`) — realism is not required.
- The file will be executed manually or via `make seed LOCAL=1` (IMP-02), not auto-run on container start.

## Verification

1. Start the local ClickHouse container (`make up`).
2. Confirm `github_events` exists and is empty or truncate it.
3. Execute the seed file:
   ```bash
   docker compose exec -T clickhouse clickhouse-client --multiquery < db/clickhouse/init/03_seed_local.sql
   ```
4. Check row count matches the number of INSERTs in the file.
5. Run the ghost-contributor query and confirm at least one repo returns ghost actors.

## Notes

- Created 2026-04-09 as the first task of Epic 8 - Improvements.
- Motivated by workshop environments with limited or no internet access where the S3-backed seed is unreliable.
