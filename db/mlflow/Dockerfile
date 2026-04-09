FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MLFLOW_HOST=0.0.0.0 \
    MLFLOW_PORT=5002 \
    MLFLOW_BACKEND_STORE_URI=sqlite:////mlflow/mlflow.db \
    MLFLOW_DEFAULT_ARTIFACT_ROOT=mlflow-artifacts:/ \
    MLFLOW_TRACKING_URI=http://127.0.0.1:5002 \
    MLFLOW_EXPERIMENT_NAME=ghost-contributors \
    GIT_PYTHON_REFRESH=quiet

WORKDIR /mlflow

RUN pip install --no-cache-dir mlflow==3.10.1

RUN mkdir -p /mlflow/artifacts /mlflow/init

COPY init/setup.sh /mlflow/init/setup.sh

RUN chmod +x /mlflow/init/setup.sh

EXPOSE 5002

VOLUME ["/mlflow"]

CMD ["sh", "-lc", "mkdir -p /mlflow/artifacts && mlflow server --host ${MLFLOW_HOST} --port ${MLFLOW_PORT} --backend-store-uri ${MLFLOW_BACKEND_STORE_URI} --default-artifact-root ${MLFLOW_DEFAULT_ARTIFACT_ROOT} & server_pid=$!; /mlflow/init/setup.sh; wait $server_pid"]
