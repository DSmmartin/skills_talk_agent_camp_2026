---
id: INF-03
name: Seed Script for GitHub Archive Pull Request Sample
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Implement repeatable ClickHouse seeding for an approximately 5M-row pull request sample.
---

# INF-03 - Seed Script for GitHub Archive Pull Request Sample

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L613)

## Objective

Create the ClickHouse seed script that loads a realistic GitHub Archive pull request dataset slice into `github_events` so the demo has meaningful local data to query.

## Description

This task defines the data-loading step for the pre-migration ClickHouse schema introduced in `INF-02`. Its purpose is to populate `github_events` with an approximately 5 million row sample focused on pull request activity, giving the NL2SQL demo enough scale to produce realistic answers without requiring the full public dataset.

The seed task should remain focused on acquisition and ingestion of the sample slice only. It should prepare a repeatable loading path that matches the current `github_events` table contract, especially the pre-migration `merged UInt8` column, while leaving orchestration, Makefile targets, and later migration behavior to other tasks.

## Scope

- Create the seed script at `db/clickhouse/init/02_seed_data.sh`.
- Load an approximately 5 million row sample into `github_events`.
- Use a GitHub Archive source slice appropriate for local development and demo repeatability.
- Filter or transform source data so the loaded rows align with the pre-migration table schema from `INF-02`.
- Keep the seed logic focused on pull request event data used by the demo queries.
- Make the loading procedure explicit enough to be reused later by `make seed`.

## Out Of Scope

- Changing the `github_events` table schema.
- Implementing the `merged` to `merged_at` migration.
- Wiring the seed script into `docker-compose.yml` or `Makefile`.
- Creating ChromaDB seed data or vector embeddings.
- Writing agent-facing schema YAML or RAG documents.
- Performing platform-wide cold-start verification.

## Deliverables

- A seed script at `db/clickhouse/init/02_seed_data.sh`.
- A documented loading approach for an approximately 5 million row GitHub Archive pull request sample.
- Seed logic compatible with the pre-migration `github_events` schema, including `merged UInt8`.
- A backlog task artifact at `backlog/INF-03.md` that records the task scope, outputs, and status.

## Acceptance Criteria

- `db/clickhouse/init/02_seed_data.sh` exists.
- The seed script targets the local ClickHouse `github_events` table created in `INF-02`.
- The loading flow is designed to populate approximately 5 million pull request-related rows.
- The loaded fields map to the pre-migration schema without requiring schema changes.
- The data source or slice selection is concrete enough to support repeatable local seeding.
- The task does not absorb compose wiring, Makefile integration, migration logic, or vector seeding responsibilities.

## Dependencies

- `INF-01` completed so the ClickHouse image context exists.
- `INF-02` completed so the `github_events` table schema already exists.
- Access to the GitHub Archive sample or public ClickHouse-backed source used for local seeding.

## Assumptions

- The demo only needs a representative subset of GitHub Archive, not the full dataset.
- An approximate target of 5 million rows is acceptable as long as the slice remains realistic and repeatable.
- Pull request-oriented records are sufficient for the initial demo questions and screenshots.
- The seed logic can assume the pre-migration `github_events` schema is already present before execution.

## Verification

Procedure used to verify the task against a live ClickHouse container:

1. Build the local ClickHouse image from `db/clickhouse/`.
2. Create a fresh Docker volume for ClickHouse data.
3. Start a live container from the built image.
4. Confirm `clickhouse-client` responds inside the container.
5. Copy `01_create_table.sql` and `02_seed_data.sh` into the container.
6. Create the `github_events` table inside the container.
7. Execute the seed script with a smaller smoke-test target using `GITHUB_ARCHIVE_TARGET_ROWS=1000` and `GITHUB_ARCHIVE_SOURCE_SUFFIXES="aa"`.
8. Query the seeded table to confirm row count, event type distribution, and live schema compatibility.

Commands used:

```bash
docker build -t skills-talk-clickhouse:inf03 db/clickhouse
docker volume create skills-talk-clickhouse-seed-data
docker run -d --name skills-talk-clickhouse-seed -v skills-talk-clickhouse-seed-data:/var/lib/clickhouse skills-talk-clickhouse:inf03
docker exec skills-talk-clickhouse-seed clickhouse-client --query 'SELECT 1'
docker cp db/clickhouse/init/01_create_table.sql skills-talk-clickhouse-seed:/tmp/01_create_table.sql
docker cp db/clickhouse/init/02_seed_data.sh skills-talk-clickhouse-seed:/tmp/02_seed_data.sh
docker exec skills-talk-clickhouse-seed sh -lc 'clickhouse-client --multiquery < /tmp/01_create_table.sql'
docker exec skills-talk-clickhouse-seed sh -lc 'chmod +x /tmp/02_seed_data.sh && GITHUB_ARCHIVE_TARGET_ROWS=1000 GITHUB_ARCHIVE_SOURCE_SUFFIXES="aa" /tmp/02_seed_data.sh'
docker exec skills-talk-clickhouse-seed clickhouse-client --query "SELECT count(), min(created_at), max(created_at) FROM github_events"
docker exec skills-talk-clickhouse-seed clickhouse-client --query "SELECT event_type, count() FROM github_events GROUP BY event_type ORDER BY count() DESC"
docker exec skills-talk-clickhouse-seed clickhouse-client --query "SELECT name, type FROM system.columns WHERE database = currentDatabase() AND table = 'github_events' ORDER BY position"
```

Full default execution command also run on 2026-04-07:

```bash
docker cp db/clickhouse/init/02_seed_data.sh skills-talk-clickhouse-seed:/tmp/02_seed_data.sh
docker exec skills-talk-clickhouse-seed sh -lc 'chmod +x /tmp/02_seed_data.sh && /tmp/02_seed_data.sh'
docker exec skills-talk-clickhouse-seed clickhouse-client --query "SELECT count(), min(created_at), max(created_at) FROM github_events"
docker exec skills-talk-clickhouse-seed clickhouse-client --query "SELECT event_type, count() FROM github_events GROUP BY event_type ORDER BY count() DESC"
```

Expected verification result:

- The seed script runs successfully against a live ClickHouse container.
- `github_events` contains seeded rows after execution.
- The loaded rows are `PullRequestEvent` records.
- The live table schema remains aligned with the pre-migration definition from `INF-02`.
- The script defaults remain configured for an approximately 5 million row load from `aa ab ac ad ae af ag`, even though initial verification used a smaller smoke-test target for faster execution.

## Notes

- Created on 2026-04-07 as the next executable Epic 1 task after `INF-02`.
- Completed on 2026-04-07.
- Implemented `db/clickhouse/init/02_seed_data.sh` as a repeatable ClickHouse seed script with configurable source suffixes, target row count, and truncation behavior.
- The default script configuration targets approximately 5 million pull request rows from GitHub Archive files `aa ab ac ad ae af ag`.
- Verified against a live ClickHouse container named `skills-talk-clickhouse-seed` with a 1,000-row smoke test from source file `aa`.
- A full default run was executed on 2026-04-07 and loaded exactly 5,000,000 `PullRequestEvent` rows into `github_events`.
