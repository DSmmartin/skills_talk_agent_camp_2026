#!/bin/sh

set -eu

: "${MLFLOW_TRACKING_URI:=http://127.0.0.1:5002}"
: "${MLFLOW_EXPERIMENT_NAME:=ghost-contributors}"
: "${MLFLOW_DEFAULT_ARTIFACT_ROOT:=/mlflow/artifacts}"

mkdir -p "${MLFLOW_DEFAULT_ARTIFACT_ROOT}"

python - <<'PY'
import os
import time
import urllib.error
import urllib.request

tracking_uri = os.environ["MLFLOW_TRACKING_URI"].rstrip("/")
target_url = f"{tracking_uri}/"

last_error = None
for _ in range(60):
    try:
        with urllib.request.urlopen(target_url, timeout=5):
            raise SystemExit(0)
    except urllib.error.URLError as exc:
        last_error = exc
        time.sleep(1)

raise SystemExit(f"MLflow server did not become ready at {target_url}: {last_error}")
PY

python - <<'PY'
import os

import mlflow
from mlflow import MlflowClient

tracking_uri = os.environ["MLFLOW_TRACKING_URI"]
experiment_name = os.environ["MLFLOW_EXPERIMENT_NAME"]
artifact_root = os.environ["MLFLOW_DEFAULT_ARTIFACT_ROOT"].rstrip("/")

mlflow.set_tracking_uri(tracking_uri)
client = MlflowClient()
experiment = client.get_experiment_by_name(experiment_name)

if experiment is None:
    experiment_id = client.create_experiment(
        experiment_name,
        artifact_location=f"{artifact_root}/{experiment_name}",
    )
    print(f"Created MLflow experiment {experiment_name} ({experiment_id})")
else:
    print(f"MLflow experiment {experiment_name} already exists ({experiment.experiment_id})")
PY
