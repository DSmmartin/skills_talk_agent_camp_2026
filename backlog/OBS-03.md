---
id: OBS-03
name: MLflow Run Structure — Root Run With Nested Agent Spans
epic: Epic 6 - Observability
status: [x] Done
summary: Ensure each query creates a root MLflow run so nested agent/tool spans attach to a single parent run.
---

# OBS-03 - MLflow Run Structure — Root Run With Nested Agent Spans

- Epic: Epic 6 - Observability
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md)

## Objective

Create an explicit MLflow root run per query so the agent/tool spans appear as nested runs under a single parent.

## Description

MLflow autologging already captures LLM calls, but the demo needs a single root run for each query to anchor nested spans (orchestrator → AgentRAG → AgentNL2SQL). The TUI should create and close a root run per question so the trace is organized in MLflow.

## Scope

- Create a root MLflow run per TUI query.
- Ensure the run is closed after each query (success or error).
- Include basic tags for the question or run count.
- Keep autologged nested spans intact.

## Out Of Scope

- Changing the OpenAI client setup.
- Adding new MLflow backends or storage options.
- Modifying existing test data or seed scripts.

## Deliverables

- Root MLflow run created per query in the TUI.
- Nested agent/tool spans appear under the root run in MLflow UI.
- Minimal logging/tagging to identify the query run.

## Acceptance Criteria

- Each question in the TUI creates a new MLflow run.
- Nested spans exist for LLM calls inside that run.
- Runs close cleanly even when the query fails.

## Dependencies

- OBS-04 experiment creation on container startup.
- Existing MLflow autolog setup in `agentic_system/setup.py`.

## Assumptions

- MLflow server is reachable at `MLFLOW_TRACKING_URI`.
- Autologging remains enabled and compatible with explicit root runs.

## Verification

Procedure used to verify the task after implementation:

1. Create a root run and capture the MLflow URL.
2. (Manual) Run the TUI with a live query to confirm nested spans.

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
    print(f"experiment_id={exp_id}")
    print(f"run_id={run_id}")
    print(f"run_url={tracking_uri}/#/experiments/{exp_id}/runs/{run_id}")
PY
```

Expected verification result:

- Output includes a valid `experiment_id`, `run_id`, and `run_url`.
- Manual TUI check shows nested spans under the root run when LLM calls execute.

Observed output:

- `experiment_id=1`
- `run_id=48966b01f0c74a17ab22647eb62bc387`
- `run_url=http://localhost:5002/#/experiments/1/runs/48966b01f0c74a17ab22647eb62bc387`

## Notes

- Requires OBS-05 to surface the run URL in the TUI for fast verification.
