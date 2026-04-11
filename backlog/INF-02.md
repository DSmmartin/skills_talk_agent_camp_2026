---
id: INF-02
name: ClickHouse Init SQL for Pre-Migration Schema
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Define the initial github_events ClickHouse schema for the pre-migration state.
---

# INF-02 - ClickHouse Init SQL for Pre-Migration Schema

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L612)

## Objective

Define the initial ClickHouse table schema for the demo so the database starts in the pre-migration state required for Act 1 and the later break/heal narrative.

## Description

This task introduces the `github_events` initialization SQL used by ClickHouse before any schema migration occurs. The schema must match the product backlog’s pre-migration model, including the original `merged UInt8` field that later becomes `merged_at`.

The purpose of this task is to lock down the starting database contract for the demo. It should create the table structure only, not seed data, not run migrations, and not wire service orchestration. Its output becomes the foundation for the seed task and for the migration script that intentionally breaks the system in Act 2.

## Scope

- Create the ClickHouse init SQL file under `db/clickhouse/init/`.
- Define the `github_events` table in its pre-migration form.
- Include the core fields identified in the backlog for the demo query flow.
- Use a table definition compatible with local ClickHouse startup initialization.
- Keep the schema aligned with the Act 1 and Act 2 story in `PRODUCT_BACKLOG.md`.

## Out Of Scope

- Loading any GitHub Archive sample data.
- Creating seed scripts or data download logic.
- Implementing the migration from `merged` to `merged_at`.
- Wiring the SQL file into `docker-compose.yml`.
- Creating RAG schema documents or YAML schema files for agents.
- Adding test fixtures or validation scripts.

## Deliverables

- A ClickHouse init SQL file at `db/clickhouse/init/01_create_table.sql`.
- A pre-migration `github_events` table definition that includes `merged UInt8`.
- A table definition compatible with later seed loading and migration tasks.
- A backlog task artifact at `backlog/INF-02.md` that records the task scope, outputs, and status.

## Acceptance Criteria

- `db/clickhouse/init/01_create_table.sql` exists.
- The SQL defines the `github_events` table used by the demo.
- The schema reflects the pre-migration state described in the backlog, including `merged UInt8`.
- The table definition is suitable for later data seeding in `INF-03`.
- The task does not absorb data seeding, migration logic, or compose wiring responsibilities.

## Dependencies

- `INF-01` completed so the ClickHouse build context already exists.
- Product decision to start the demo from a pre-migration schema state.
- Later `INF-03` data seeding to populate the table after creation.

## Assumptions

- ClickHouse init SQL files placed in `db/clickhouse/init/` will be used by the local infrastructure flow.
- The pre-migration schema must preserve the `merged` field specifically to support the later migration demo.
- The schema remains intentionally minimal and focused on fields required by the demo queries.

## Verification

Procedure used to verify the task against a live ClickHouse container:

1. Build the local ClickHouse image from `db/clickhouse/`.
2. Create a Docker volume for persistent ClickHouse data.
3. Start a live container from the built image.
4. Wait until `clickhouse-client` responds successfully inside the container.
5. Copy `db/clickhouse/init/01_create_table.sql` into the container.
6. Execute the SQL file with `clickhouse-client`.
7. Query ClickHouse system tables to confirm the table exists.
8. Query ClickHouse system columns to confirm the live schema and the `merged UInt8` column.

Commands used:

```bash
docker build -t skills-talk-clickhouse:inf01 db/clickhouse
docker volume create skills-talk-clickhouse-data
docker run -d --name skills-talk-clickhouse-live -v skills-talk-clickhouse-data:/var/lib/clickhouse skills-talk-clickhouse:inf01
docker exec skills-talk-clickhouse-live clickhouse-client --query 'SELECT 1'
docker cp db/clickhouse/init/01_create_table.sql skills-talk-clickhouse-live:/tmp/01_create_table.sql
docker exec skills-talk-clickhouse-live sh -lc 'clickhouse-client --multiquery < /tmp/01_create_table.sql'
docker exec skills-talk-clickhouse-live clickhouse-client --query "SELECT name FROM system.tables WHERE database = currentDatabase()"
docker exec skills-talk-clickhouse-live clickhouse-client --query "SELECT name, type FROM system.columns WHERE database = currentDatabase() AND table = 'github_events' ORDER BY position"
```

Expected verification result:

- Table `github_events` exists in the current database.
- Column `merged` exists with type `UInt8`.
- The live schema matches the pre-migration definition in `db/clickhouse/init/01_create_table.sql`.

## Notes

- Completed on 2026-04-07.
- Implemented `db/clickhouse/init/01_create_table.sql` with the pre-migration `github_events` schema, including `merged UInt8`.
- Verified against a live ClickHouse container named `skills-talk-clickhouse-live`.
- Live schema check confirmed table `github_events` exists and the `merged` column type is `UInt8`.
