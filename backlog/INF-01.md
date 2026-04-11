---
id: INF-01
name: ClickHouse Dockerfile and Persistent Volume
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Create the ClickHouse container baseline and persistence foundation for local demo data.
---

# INF-01 - ClickHouse Dockerfile and Persistent Volume

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L611)

## Objective

Create the ClickHouse container baseline for the demo so the database can be built consistently and prepared for durable local storage.

## Description

This task defines the first executable infrastructure artifact for Epic 1: the ClickHouse image definition. The goal is to establish a stable database container foundation that later tasks can build on for schema initialization, data seeding, and orchestration.

The task also makes persistence explicit. ClickHouse data must survive container restarts during the demo workflow, but the full service wiring belongs to the compose task later in the epic. This task therefore defines the image and the persistence target, while keeping orchestration boundaries clear.

## Scope

- Create the ClickHouse image definition under `db/clickhouse/`.
- Use the official ClickHouse image as the base for the local demo setup.
- Define the expected persistent data location used by the container.
- Prepare the ClickHouse build context so later tasks can add init SQL and configuration files without restructuring the folder.
- Keep the task compatible with later compose-based service wiring.

## Out Of Scope

- Writing the `github_events` table schema.
- Loading or seeding GitHub Archive data.
- Wiring the ClickHouse service into `docker-compose.yml`.
- Implementing ChromaDB or MLflow infrastructure.
- Running cross-platform cold-start validation.
- Adding migration or rollback scripts.

## Deliverables

- A ClickHouse Dockerfile at `db/clickhouse/Dockerfile`.
- A defined persistent storage target for ClickHouse data, expected to map to `/var/lib/clickhouse`.
- A prepared `db/clickhouse/` build context that supports later `init/` and `config/` additions without rework.
- A backlog task artifact at `backlog/INF-01.md` that records the task scope, expected output, and status.

## Acceptance Criteria

- `db/clickhouse/Dockerfile` exists and is intended to build the ClickHouse service image for local use.
- The Dockerfile is based on the official ClickHouse image strategy described in the product backlog.
- The persistent data location for ClickHouse is explicit and compatible with later named-volume wiring.
- The task does not absorb schema creation, seed loading, or compose orchestration responsibilities.
- The folder structure created by this task is compatible with follow-up tasks `INF-02`, `INF-03`, and `INF-07`.

## Dependencies

- `INF-00` completed so Epic 1 scope and boundaries are already defined.
- Product decision to use ClickHouse as the SQL database for the demo.
- Later compose wiring in `INF-07` to connect the persistence definition to a running service.

## Assumptions

- The implementation will use the official ClickHouse Docker image as the base layer.
- Persistent storage will be mounted through Docker Compose in a later task rather than fully wired here.
- The local demo environment remains Docker-first on macOS and Linux.

## Notes

- Completed on 2026-04-07.
- Implemented `db/clickhouse/Dockerfile` and prepared `db/clickhouse/init/` and `db/clickhouse/config/` for follow-up tasks.
