# Skills Talk AgentCamp 2026

This repository supports a workshop series about building reusable **Skills** for real projects.

The goals are:
- Learn how to structure project workflows with Skills.
- Provide practical demo implementations as inspiration and proof of value.
- Reuse the same infrastructure baseline across multiple demos (current and future).

## Infrastructure (Current Baseline)

The local infrastructure starts 3 services:

- **ClickHouse**: analytics SQL backend for demo datasets.
- **ChromaDB**: vector store for retrieval use cases.
- **MLflow**: tracking server for runs and observability.

## Requirements

- Docker Desktop (or Docker Engine) with Compose v2.
- `make`.
- Python 3.11+ (used by vector seed script).
- Internet access (required by some demo seed scripts).

## Quick Start

From repository root:

```bash
make up
make seed
make seed-vectors
```

Useful commands:

```bash
make logs
make down
make reset
```

Notes:
- If host port `5000` is busy, MLflow host port auto-falls back (`5002+`) during startup.
- Default service ports:
  ClickHouse `8123/9000`, ChromaDB `8000`, MLflow container `5000` (host may differ due to fallback).

## Technologies

- Docker / Docker Compose
- ClickHouse
- ChromaDB
- MLflow
- Python
- Makefile-based task runner

## Demos

This repo is designed to host multiple demos over time.

- **Demo 01: Ghost Contributors**
  Agentic NL2SQL demo over GitHub pull-request events, used to illustrate how Skills and developer procedures improve reliability during controlled changes (for example, schema evolution).

## More Detail

For technical infrastructure details and service-by-service purpose:
[db/README.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/db/README.md)
