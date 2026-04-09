# Infrastructure Details (`/db`)

This folder contains the container build/runtime assets for the three local infrastructure services used by the scenario.

## Service Overview

### `clickhouse/`
Purpose:
- Primary SQL engine for analytics queries over GitHub pull-request events.

Key files:
- `clickhouse/Dockerfile`: local image baseline from `clickhouse/clickhouse-server`.
- `clickhouse/init/01_create_table.sql`: table creation script for `github_events` (pre-migration schema).
- `clickhouse/init/02_seed_data.sh`: loads sample PR events (target default: 5,000,000 rows).
- `clickhouse/config/`: custom server config mount point.

How it is used:
- Table is initialized automatically on first startup.
- Seeding is explicit (manual) via `make seed`.

### `vectordb/`
Purpose:
- Retrieval store for schema context and NL2SQL examples used by the agent flow.

Key files:
- `vectordb/Dockerfile`: local ChromaDB image baseline.
- `vectordb/init/seed_vectors.py`: deterministic seeding script via Chroma HTTP API.
- `vectordb/collections/schema_docs/`: schema-oriented documents.
- `vectordb/collections/qa_examples/`: Q&A examples used for retrieval behavior.

How it is used:
- Container provides vector storage.
- Content seeding is explicit via `make seed-vectors`.

### `mlflow/`
Purpose:
- Tracking and observability backend for runs/experiments.

Key files:
- `mlflow/Dockerfile`: MLflow server image (`mlflow==2.21.3`).
- `mlflow/init/setup.sh`: startup bootstrap for experiment creation.

How it is used:
- Runs MLflow tracking server on container port `5002`.
- Uses SQLite backend and artifacts under `/mlflow`.
- Experiment `ghost-contributors` is created on startup if missing.

## Runtime Wiring

All services are wired in root `docker-compose.yml` with named volumes for persistence:

- `clickhouse_data`
- `chromadb_data`
- `mlflow_data`

Primary workflow is driven by root `Makefile`:

```bash
make up
make seed
make seed-vectors
make down
```

## Design Intent

- Keep service responsibilities clear and decoupled.
- Keep data seeding explicit and repeatable.
- Keep local startup simple while preserving production-like boundaries.
