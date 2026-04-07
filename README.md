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

An agentic NL2SQL system that answers natural language questions about GitHub contributor behaviour using the **AgentAsTools** pattern. The demo has three acts:

| Act | What happens |
|-----|-------------|
| **Act 1 — It works** | Agent answers the ghost contributor question correctly via `AgentRAG` + `AgentNL2SQL` |
| **Act 2 — It breaks** | A schema migration renames `merged UInt8` → `merged_at DateTime NULL`; the system silently returns wrong answers across all four layers |
| **Act 3 — It heals** | Developer runs `schema-sync`; it detects drift and patches prompts, RAG, schema docs, and tool descriptions in one pass |

The key point: **Act 3 shows how to formalise a developer procedure for a fully expected situation** — schema migrations are predictable; `schema-sync` is the repeatable procedure for handling them.

**Stack:** OpenAI Agents SDK · ClickHouse · ChromaDB · MLflow · Textual TUI · Python 3.14

```bash
make up && make seed && make seed-vectors
python agentic_system/main.py
```

→ Full details: [`agentic_system/README.md`](agentic_system/README.md)

## More Detail

For technical infrastructure details and service-by-service purpose:
[db/README.md](db/README.md)
