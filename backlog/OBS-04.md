---
id: OBS-04
name: MLflow Experiment Pre-Created on Container Startup
epic: Epic 6 - Observability
status: [x] Done
summary: Ensure the configured MLflow experiment exists as soon as the MLflow container starts.
---

# OBS-04 - MLflow Experiment Pre-Created on Container Startup

- Epic: Epic 6 - Observability
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md)

## Objective

Have the MLflow experiment created automatically when the MLflow container starts.

## Description

The demo relies on a consistent experiment name. The MLflow container should ensure the experiment exists before any runs are created so the UI is ready and stable.

## Scope

- Bootstrap MLflow experiment creation on container startup.
- Use `MLFLOW_EXPERIMENT_NAME` as the canonical experiment name.
- Ensure idempotent behavior (create if missing, otherwise no-op).

## Out Of Scope

- Changing the MLflow tracking backend.
- Adding multi-tenant experiment management.

## Deliverables

- Startup script that creates or verifies the experiment.
- Clear output in container logs indicating experiment status.

## Acceptance Criteria

- Experiment exists immediately after MLflow service starts.
- Startup is idempotent with clear logs.

## Dependencies

- MLflow container startup script.

## Assumptions

- MLflow server is available at the configured tracking URI during startup.

## Verification

Procedure used to verify the task after implementation:

1. Query MLflow for the configured experiment.

```bash
MLFLOW_TRACKING_URI=http://localhost:5002 \
MLFLOW_EXPERIMENT_NAME=ghost-contributors-demo \
uv run python - <<'PY'
import os
import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
client = MlflowClient()
exp = client.get_experiment_by_name(os.environ["MLFLOW_EXPERIMENT_NAME"])
print(exp is not None)
print(exp.experiment_id if exp else "missing")
PY
```

Expected verification result:

- The script prints `True` and a valid experiment id.

Observed output:

- `True`
- `1`

## Notes

- The MLflow container init script should handle creation on startup.
