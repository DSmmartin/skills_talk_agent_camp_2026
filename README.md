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

### Demo 01 — Ghost Contributors

> *"Show me repositories where users opened PRs but never got one merged — the ghost contributors"*

An agentic NL2SQL system that answers natural language questions about GitHub contributor behaviour using the **AgentAsTools** pattern.

Current status (2026-04-08): **Epics 1–5 complete** (Infrastructure, Agentic System, Migration Scripts, Developer Tools, Tests).

| Act | What happens | Primary command |
|-----|-------------|-----------------|
| **Act 1 — It works** | Agent answers the ghost contributor question correctly via `AgentRAG` + `AgentNL2SQL`. | `uv run python agentic_system/main.py` |
| **Act 2 — It breaks** | A schema migration introduces `merged_at Nullable(DateTime)` and legacy `merged = 1` logic starts returning 0 rows silently across four layers. | `make migrate` |
| **Act 3 — It heals** | `schema_sync` patches YAML contract, ChromaDB chunks, NL2SQL prompt, and RAG prompt in one procedure. Skill progression examples live in `dev_tools/skill_examples/`. | `make schema-sync` |

The key point: **Act 3 formalises a predictable developer response**. Schema migrations are expected events, and `schema_sync` makes the repair path repeatable.

**Stack:** OpenAI Agents SDK · ClickHouse · ChromaDB · MLflow · Textual TUI · Python 3.14


## More Detail

- Product backlog and epic status: [`PRODUCT_BACKLOG.md`](PRODUCT_BACKLOG.md)
- Agent architecture and runtime details: [`agentic_system/README.md`](agentic_system/README.md)
- Act 3 developer tools and skill progression: [`dev_tools/README.md`](dev_tools/README.md)
- Infrastructure and service-level details: [`db/README.md`](db/README.md)
