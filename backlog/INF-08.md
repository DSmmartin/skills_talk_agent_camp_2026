---
id: INF-08
name: .env.example and Makefile with Required Infrastructure Targets
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Standardize infrastructure workflows with .env defaults and required Make targets.
---

# INF-08 - .env.example and Makefile with Required Infrastructure Targets

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L618)

## Objective

Provide a standard local command surface for infrastructure workflows by adding `.env.example` defaults and a root `Makefile` with the required targets.

## Description

This task defines the developer entrypoints for Epic 1 infrastructure operations. It converts direct script and compose usage into a consistent `make` interface while keeping compatibility with the existing infra scripts (`setup_infra.sh`, `cleanup_infra.sh`, ClickHouse seed script, and Chroma seed script).

The target list follows the backlog requirement: `up`, `down`, `seed`, `seed-vectors`, `migrate`, `rollback`, `reset`, and `logs`. Since migration scripts are planned in Epic 3, `migrate` and `rollback` are implemented with explicit guards that fail with a clear message until those scripts exist.

## Scope

- Create root `.env.example` with local infra defaults.
- Create root `Makefile` with all required targets.
- Wire `up` and `reset` to existing infra setup and cleanup scripts.
- Wire `seed` to run ClickHouse seed script inside the running compose service.
- Wire `seed-vectors` to run the Chroma seed utility from the repository root.
- Wire `logs` to print compose service logs.
- Add guarded placeholder behavior for `migrate` and `rollback` until Epic 3 scripts are implemented.

## Out Of Scope

- Implementing migration logic (`scripts/migrate_schema.py`) or rollback logic (`scripts/rollback_schema.py`).
- Adding `docker-compose.override.yml.example`.
- Changing service definitions in `docker-compose.yml`.
- Cross-platform verification for macOS Intel and Linux (handled by `INF-09`).

## Deliverables

- `.env.example` with project and infra defaults.
- Root `Makefile` with targets:
  `up`, `down`, `seed`, `seed-vectors`, `migrate`, `rollback`, `reset`, `logs`.
- Guarded error messages for `migrate` and `rollback` when scripts are missing.
- Backlog traceability artifact at `backlog/INF-08.md`.

## Acceptance Criteria

- `.env.example` exists and includes infra defaults used by make workflows.
- `Makefile` exists and defines all required targets from the backlog.
- `make up`, `make seed`, `make seed-vectors`, `make logs`, and `make down` execute successfully against a live stack.
- `make migrate` and `make rollback` fail fast with explicit “not available yet” messages when corresponding scripts do not exist.
- `make reset` is defined and references cleanup + setup workflow.

## Dependencies

- `INF-01` through `INF-07` completed (service images, init scripts, and compose wiring already available).
- Existing scripts: `scripts/setup_infra.sh`, `scripts/cleanup_infra.sh`, `db/clickhouse/init/02_seed_data.sh`, and `db/vectordb/init/seed_vectors.py`.
- Epic 3 migration tasks for future activation of `migrate` and `rollback`.

## Assumptions

- Developers run targets from repository root.
- `.env.example` is copied to `.env` when local customization is needed.
- Default host ports may be busy; startup should rely on `setup_infra.sh` auto-fallback behavior for MLflow when default port `5000` is occupied.

## Verification

Procedure used to verify the task:

1. Confirm target discovery with `make help`.
2. Start the stack with `make up`; verify startup succeeds and MLflow host-port fallback is applied when `5000` is occupied.
3. Execute ClickHouse seed workflow with `make seed GITHUB_ARCHIVE_TARGET_ROWS=1000`.
4. Execute Chroma seed workflow with `make seed-vectors`.
5. Read service logs with `make logs`.
6. Validate placeholder target behavior with `make migrate` and `make rollback` (expected failure with explicit message).
7. Confirm reset target wiring with `make -n reset`.
8. Stop stack with `make down`.

Commands used:

```bash
make help
make up
make seed GITHUB_ARCHIVE_TARGET_ROWS=1000
make seed-vectors
make logs
make migrate
make rollback
make -n reset
make down
```

Observed results:

- `make up` succeeded and selected MLflow host port `5002` because port `5000` was in use.
- `make seed` inserted exactly 1,000 rows into `github_events`.
- `make seed-vectors` seeded `schema_docs` and `qa_examples` collections and returned expected top QA matches.
- `make logs` returned service logs for ClickHouse, ChromaDB, and MLflow.
- `make migrate` and `make rollback` failed with explicit messages indicating scripts are planned in `MIG-01` and `MIG-03`.
- `make -n reset` showed cleanup + setup command sequence.
- `make down` removed running containers and network successfully.

## Notes

- Created on 2026-04-07 as the next Epic 1 task after `INF-07`.
- Completed on 2026-04-07.
- Implemented `.env.example` and root `Makefile` for standardized infra workflows.
- Updated `Makefile` startup behavior to preserve `setup_infra.sh` automatic MLflow fallback when using default port `5000`.
