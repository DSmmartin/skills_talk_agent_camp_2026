---
id: INF-07
name: docker-compose.yml Wiring for ClickHouse, ChromaDB, and MLflow
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Wire ClickHouse, ChromaDB, and MLflow into one local compose stack with persistence.
---

# INF-07 - docker-compose.yml Wiring for ClickHouse, ChromaDB, and MLflow

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L617)

## Objective

Create the local `docker-compose.yml` so the three infrastructure services can be started together with the correct build contexts, ports, persistence, and startup wiring.

## Description

This task defines the first integrated runtime for Epic 1. Its purpose is to connect the already implemented ClickHouse, ChromaDB, and MLflow service baselines into a single local compose stack that can be brought up consistently during development and demos.

The compose file should wire build contexts, host ports, and named volumes while preserving the boundaries already established by earlier tasks. In particular, ClickHouse should initialize the table schema at startup, but it should not automatically run the 5 million row seed script because data seeding remains a separate explicit step.

## Scope

- Create `docker-compose.yml` at the repository root.
- Wire the `clickhouse`, `chromadb`, and `mlflow` services to their local build contexts.
- Expose the expected host ports for all three services.
- Define named volumes for persistent service data.
- Mount the ClickHouse table init SQL into the entrypoint init directory.
- Keep the ClickHouse seed script available to the service without auto-running it on stack startup.

## Out Of Scope

- Creating `.env.example` or `Makefile` targets.
- Running the ClickHouse 5 million row seed as part of stack startup.
- Running the ChromaDB vector seed as part of stack startup.
- Application-level agent wiring or tracing setup.
- Cross-platform cold-start validation.
- Override files or cloud deployment concerns.

## Deliverables

- A root-level `docker-compose.yml`.
- Compose service wiring for `clickhouse`, `chromadb`, and `mlflow`.
- Named volumes for ClickHouse, ChromaDB, and MLflow persistence.
- ClickHouse startup wiring that runs `01_create_table.sql` automatically but keeps `02_seed_data.sh` manual.
- A cleanup utility at `scripts/cleanup_infra.sh` to tear down local infra containers and optionally volumes.
- A setup utility at `scripts/setup_infra.sh` to start the stack with optional clean-first and configurable MLflow host port.
- A backlog task artifact at `backlog/INF-07.md` that records the task scope, outputs, and status.

## Acceptance Criteria

- `docker-compose.yml` exists.
- The compose file builds all three local images from `db/clickhouse`, `db/vectordb`, and `db/mlflow`.
- The compose file exposes the expected service ports from the backlog.
- Named volumes are defined for persistent data across the three services.
- ClickHouse schema initialization is wired without auto-running the large data seed.
- The compose stack can be brought up successfully with all three services running.

## Dependencies

- `INF-01` through `INF-06` completed so each service has its own image baseline.
- Product decision to run the local demo stack with Docker Compose.
- Later `INF-08` work to wrap compose commands in `.env.example` and `Makefile` targets.

## Assumptions

- The local development flow uses Docker Compose v2.
- Host ports `8123`, `9000`, `8000`, and `5000` are acceptable defaults for the stack.
- ClickHouse should allow local network access for the default user in this demo setup.
- The compose file should stay self-contained and not depend on `.env.example` yet.

## Verification

Procedure used to verify the task against a live compose stack:

1. Validate compose syntax with `docker compose config`.
2. Attempt stack startup with `docker compose up -d` using the committed `docker-compose.yml`.
3. Confirm ClickHouse and ChromaDB start; detect host port conflict for `5000` on this machine.
4. Run a temporary verification compose file (outside the repo) that keeps service wiring identical but maps MLflow as `5002:5000`.
5. Bring up the full three-service verification stack and confirm all containers are `Up`.
6. Validate ClickHouse startup init behavior:
   schema table `github_events` exists,
   row count is `0` (seed script not auto-run),
   `02_seed_data.sh` is present for manual execution.
7. Validate ChromaDB runtime and persistence path:
   `CHROMA_PERSIST_PATH=/chroma/chroma`
   and `chroma.sqlite3` exists in that directory.
8. Validate MLflow runtime and bootstrap:
   experiment `ghost-contributors-demo` exists,
   artifact location is `/mlflow/artifacts/ghost-contributors-demo`,
   and a smoke run logs successfully with `task=INF-07` and `verification=1.0`.
9. Validate the cleanup utility:
   dry-run output is correct and a real run removes running infra containers for this project and verification stacks.
10. Validate the setup utility:
    dry-run output is correct and a real run starts the full compose stack.

Commands used:

```bash
docker compose config
docker compose up -d
docker compose down
docker compose -f /tmp/skills-talk-inf07-verify-compose.yml -p skills_talk_inf07_verify up -d
docker compose -f /tmp/skills-talk-inf07-verify-compose.yml -p skills_talk_inf07_verify ps
docker exec skills_talk_inf07_verify-clickhouse-1 clickhouse-client --query "SELECT name FROM system.tables WHERE database = currentDatabase() AND name = 'github_events'"
docker exec skills_talk_inf07_verify-clickhouse-1 clickhouse-client --query "SELECT count() FROM github_events"
docker exec skills_talk_inf07_verify-clickhouse-1 sh -lc 'test -f /opt/demo/init/02_seed_data.sh && echo seed_script_present'
docker exec skills_talk_inf07_verify-chromadb-1 sh -lc 'printf "%s\n" "$CHROMA_PERSIST_PATH" && ls -la /chroma/chroma'
docker exec skills_talk_inf07_verify-mlflow-1 python -c "import mlflow; from mlflow import MlflowClient; mlflow.set_tracking_uri('http://127.0.0.1:5000'); client = MlflowClient(); exp = client.get_experiment_by_name('ghost-contributors-demo'); print(exp.experiment_id if exp else 'missing'); print(exp.artifact_location if exp else 'missing')"
docker exec skills_talk_inf07_verify-mlflow-1 python -c "import mlflow; from mlflow import MlflowClient; mlflow.set_tracking_uri('http://127.0.0.1:5000'); mlflow.set_experiment('ghost-contributors-demo');
with mlflow.start_run(run_name='inf07_compose_smoke') as run:
    mlflow.log_param('task', 'INF-07');
    mlflow.log_metric('verification', 1.0);
    print(run.info.run_id)
client = MlflowClient(); exp = client.get_experiment_by_name('ghost-contributors-demo'); runs = client.search_runs([exp.experiment_id], max_results=1, order_by=['attributes.start_time DESC']); print(runs[0].data.params.get('task')); print(runs[0].data.metrics.get('verification'))"
scripts/cleanup_infra.sh --dry-run
scripts/cleanup_infra.sh
scripts/setup_infra.sh --dry-run
scripts/setup_infra.sh
```

Expected verification result:

- `docker-compose.yml` is valid and build contexts resolve.
- Full three-service startup succeeds when host-port conflicts are absent.
- ClickHouse and ChromaDB startup wiring works as expected.
- MLflow starts with SQLite backend and default artifact root.
- The compose wiring preserves explicit/manual seed boundaries for ClickHouse.
- The cleanup utility can tear down project infra containers, and optionally supports `--volumes` for persistent-data cleanup.
- The setup utility can start the stack, optionally clean first, and handle MLflow host port selection.

## Notes

- Created on 2026-04-07 as the next Epic 1 task after `INF-06`.
- Completed on 2026-04-07.
- Implemented root `docker-compose.yml` wiring for `clickhouse`, `chromadb`, and `mlflow` with named volumes.
- ClickHouse schema init is mounted at `/docker-entrypoint-initdb.d/01_create_table.sql`.
- ClickHouse seed script is mounted at `/opt/demo/init/02_seed_data.sh` but is not auto-executed.
- Added `scripts/cleanup_infra.sh` with explicit volume modes:
  `--keep-volumes` (default) and `--clear-volumes`,
  optional `--clear-images`,
  plus `--start-after` to bring the stack back up after cleanup.
- Added `scripts/setup_infra.sh` as the startup counterpart:
  supports `--clean-first`, `--clear-volumes`, and `--mlflow-host-port`.
- On this host, port `5000` is occupied by macOS `ControlCenter`; startup verification uses an automatic fallback MLflow host port in range `5002..5010` (currently `5003`).
