---
id: INF-06
name: MLflow Dockerfile and Tracking Server with SQLite Backend
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Create a local MLflow tracking baseline with SQLite backend and persistent artifacts.
---

# INF-06 - MLflow Dockerfile and Tracking Server with SQLite Backend

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L616)

## Objective

Create the MLflow container baseline for the demo so experiment runs can be tracked through a local MLflow server backed by SQLite and a persistent artifact directory.

## Description

This task defines the observability server baseline for Epic 1. Its purpose is to provide a local MLflow tracking service that can persist experiment metadata in SQLite and store artifacts under the shared `/mlflow` volume path planned in the backlog.

The task should include both the image definition and the initial setup script that prepares the default experiment and artifact root for the demo. It should remain focused on the tracking server foundation only, not compose wiring, not agent-side tracing instrumentation, and not evaluation flows.

## Scope

- Create the MLflow image definition under `db/mlflow/`.
- Configure MLflow to run a tracking server on port `5000`.
- Use a SQLite backend store persisted under `/mlflow`.
- Define the default artifact root under `/mlflow/artifacts`.
- Create the initialization script at `db/mlflow/init/setup.sh`.
- Bootstrap the demo experiment required by the backlog.

## Out Of Scope

- Wiring MLflow into `docker-compose.yml`.
- Applying MLflow tracing decorators in the application code.
- Creating demo runs from the orchestrator or agents.
- Implementing dashboards, evaluations, or reports.
- Cross-platform cold-start validation.
- Azure or remote MLflow deployment concerns.

## Deliverables

- An MLflow Dockerfile at `db/mlflow/Dockerfile`.
- An initialization script at `db/mlflow/init/setup.sh`.
- A local MLflow tracking server configuration using a SQLite backend under `/mlflow`.
- A default artifact root under `/mlflow/artifacts`.
- A backlog task artifact at `backlog/INF-06.md` that records the task scope, outputs, and status.

## Acceptance Criteria

- `db/mlflow/Dockerfile` exists and builds the local MLflow image.
- `db/mlflow/init/setup.sh` exists and prepares the default experiment for the demo.
- The MLflow server runs on port `5000`.
- The backend store persists in SQLite under `/mlflow`.
- The artifact root persists under `/mlflow/artifacts`.
- The task does not absorb compose wiring or application-level tracing work.

## Dependencies

- `INF-00` completed so Epic 1 scope and boundaries are already defined.
- Product decision to use MLflow as the experiment tracking server for the demo.
- Later compose wiring in `INF-07` and agent-side instrumentation in `AGT-07`.

## Assumptions

- The local demo environment remains Docker-first on macOS and Linux.
- MLflow metadata should be stored in SQLite for local simplicity.
- The demo experiment name should align with the backlog example `ghost-contributors-demo`.
- Persistent MLflow state should live under `/mlflow` so compose can mount a single named volume later.

## Verification

Procedure used to verify the task against a live MLflow container:

1. Build the local MLflow image from `db/mlflow/`.
2. Create a Docker volume for persistent MLflow state.
3. Start a live container from the built image with `/mlflow` mounted from the named volume.
4. Inspect container logs to confirm the MLflow server is listening on port `5000` and that the setup script created or reused `ghost-contributors-demo`.
5. Inspect `/mlflow` inside the container to confirm `mlflow.db` and the artifact directory exist.
6. Query the live MLflow server from inside the container to confirm the default experiment exists and points to `/mlflow/artifacts/ghost-contributors-demo`.
7. Log a smoke run to the live server and confirm the latest run contains parameter `task=INF-06` and metric `verification=1.0`.

Commands used:

```bash
docker build -t skills-talk-mlflow:inf06 db/mlflow
docker volume create skills-talk-mlflow-data
docker run -d --name skills-talk-mlflow-live -p 5001:5000 -v skills-talk-mlflow-data:/mlflow skills-talk-mlflow:inf06
docker logs skills-talk-mlflow-live
docker exec skills-talk-mlflow-live sh -lc 'ls -la /mlflow /mlflow/artifacts'
docker exec skills-talk-mlflow-live python -c "import mlflow; from mlflow import MlflowClient; mlflow.set_tracking_uri('http://127.0.0.1:5000'); client = MlflowClient(); exp = client.get_experiment_by_name('ghost-contributors-demo'); print(exp.experiment_id if exp else 'missing'); print(exp.artifact_location if exp else 'missing')"
docker exec skills-talk-mlflow-live python -c "import mlflow; from mlflow import MlflowClient; mlflow.set_tracking_uri('http://127.0.0.1:5000'); mlflow.set_experiment('ghost-contributors-demo');
with mlflow.start_run(run_name='inf06_smoke') as run:
    mlflow.log_param('task', 'INF-06');
    mlflow.log_metric('verification', 1.0);
    print(run.info.run_id)
client = MlflowClient(); exp = client.get_experiment_by_name('ghost-contributors-demo'); runs = client.search_runs([exp.experiment_id], max_results=1, order_by=['attributes.start_time DESC']); print(len(runs)); print(runs[0].data.params.get('task')); print(runs[0].data.metrics.get('verification'))"
```

Expected verification result:

- The MLflow image builds successfully from `db/mlflow/Dockerfile`.
- The live server starts and listens on port `5000`.
- `/mlflow/mlflow.db` exists and the artifact directory exists under `/mlflow/artifacts`.
- The default experiment `ghost-contributors-demo` exists with artifact location `/mlflow/artifacts/ghost-contributors-demo`.
- A smoke run can be logged successfully through the live tracking server.

## Notes

- Created on 2026-04-07 as the next Epic 1 task after `INF-05`.
- Completed on 2026-04-07.
- Implemented `db/mlflow/Dockerfile` and `db/mlflow/init/setup.sh`.
- The container runs `mlflow server` on port `5000` with backend store `sqlite:////mlflow/mlflow.db`.
- The default artifact root is `/mlflow/artifacts`.
- The setup script bootstraps the `ghost-contributors-demo` experiment on container startup.
- Verified against a live MLflow container named `skills-talk-mlflow-live`.
