---
id: OBS-05
name: TUI Panel Showing MLflow Run URL
epic: Epic 6 - Observability
status: [x] Done
summary: Display the MLflow run link for the current query directly in the Textual TUI.
---

# OBS-05 - TUI Panel Showing MLflow Run URL

- Epic: Epic 6 - Observability
- Priority: P1
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md)

## Objective

Expose the MLflow run URL for the current query in the TUI so presenters can open the trace quickly.

## Description

The demo benefits from a fast link to the active MLflow run. The TUI should show the run id and URL for the most recent query so the presenter can open the MLflow trace without manual search.

## Scope

- Add a dedicated TUI panel for the MLflow run.
- Update the panel when a new query starts.
- Show the run id and full MLflow UI URL.

## Out Of Scope

- Building a full MLflow UI inside the TUI.
- Persisting run links across sessions.

## Deliverables

- New MLflow panel in the Textual TUI layout.
- Panel updates on each query with the latest run id and URL.

## Acceptance Criteria

- TUI displays MLflow run URL for the current query.
- URL matches the tracking server and experiment for the run.

## Dependencies

- OBS-03 root run creation in the TUI.
- MLflow tracking URI configured in settings.

## Assumptions

- MLflow server is reachable during the demo.

## Verification

Procedure used to verify the task after implementation:

1. Generate a run URL and confirm the format.
2. (Manual) Launch the TUI and confirm the MLflow panel shows the same URL format.

```bash
MLFLOW_TRACKING_URI=http://localhost:5002 \
MLFLOW_EXPERIMENT_NAME=ghost-contributors-demo \
uv run python - <<'PY'
import os
import mlflow
from mlflow import MlflowClient

tracking_uri = os.environ["MLFLOW_TRACKING_URI"].rstrip("/")
experiment_name = os.environ["MLFLOW_EXPERIMENT_NAME"]
mlflow.set_tracking_uri(tracking_uri)
client = MlflowClient()
exp = client.get_experiment_by_name(experiment_name)
exp_id = exp.experiment_id if exp else client.create_experiment(experiment_name)

with mlflow.start_run(run_name="obs-verify") as run:
    run_id = run.info.run_id
    print(f"run_url={tracking_uri}/#/experiments/{exp_id}/runs/{run_id}")
PY
```

Expected verification result:

- The MLflow panel prints a run id and a clickable URL for the current query.

Observed output:

- `run_url=http://localhost:5002/#/experiments/1/runs/48966b01f0c74a17ab22647eb62bc387`
