# Skills Talk AgentCamp 2026

This repository supports building reusable **Skills** for real projects.

> Extended guide and materials: [`NOT_TO_READ_ASSISTANT/AUDIENCE_GUIDE.md`](NOT_TO_READ_ASSISTANT/AUDIENCE_GUIDE.md)

The goals are:
- Learn how to structure project workflows with Skills.
- Provide practical implementations as inspiration and proof of value.
- Reuse the same infrastructure baseline across multiple scenarios over time.

## Infrastructure (Current Baseline)

The local infrastructure starts 3 services:

- **ClickHouse**: analytics SQL backend for datasets.
- **ChromaDB**: vector store for retrieval use cases.
- **MLflow**: tracking server for runs and observability.

## Requirements

- Docker Desktop (or Docker Engine) with Compose v2.
- `make`.
- Python 3.11+ (used by vector seed script).
- Internet access (required for `make seed`; not required for `make seed LOCAL=1`).

## Quick Start

From repository root:

```bash
make up
make seed           # ~5M rows from GitHub Archive (requires internet)
# make seed LOCAL=1 # offline fallback: 18 controlled rows, ghost-contributor pattern intact
make seed-vectors
```

Useful commands:

```bash
make logs
make down
make reset
```

Notes:
- Default service ports:
  ClickHouse `8123/9000`, ChromaDB `8000`, MLflow `5002`.

## Technologies

- Docker / Docker Compose
- ClickHouse
- ChromaDB
- MLflow
- Python
- Makefile-based task runner

## Reference Scenario

This repo is designed to host multiple scenarios over time.

### Scenario 01 — Ghost Contributors

> *"Show me repositories where users opened PRs but never got one merged — the ghost contributors"*

An agentic NL2SQL system that answers natural language questions about GitHub contributor behaviour using the **AgentAsTools** pattern.

Current status (2026-04-08): **Epics 1–5 complete** (Infrastructure, Agentic System, Migration Scripts, Developer Tools, Tests).

| Phase | What happens | Primary command |
|-----|-------------|-----------------|
| **Phase 1 — Baseline** | Agent answers the ghost contributor question correctly via `AgentRAG` + `AgentNL2SQL`. | `uv run python agentic_system/main.py` |
| **Phase 2 — Migration Break** | A schema migration introduces `merged_at Nullable(DateTime)` and legacy `merged = 1` logic starts returning 0 rows silently across four layers. | `make migrate` |
| **Phase 3 — Recovery** | `schema_sync` patches YAML contract, ChromaDB chunks, NL2SQL prompt, and RAG prompt in one procedure. Skill progression examples live in `dev_tools/skill_examples/`. | `make schema-sync` |

The key point: **Phase 3 formalises a predictable developer response**. Schema migrations are expected events, and `schema_sync` makes the repair path repeatable.

**Stack:** OpenAI Agents SDK · ClickHouse · ChromaDB · MLflow · Textual TUI · Python 3.14


## More Detail

- Extended guide (setup, architecture, full walkthrough): [`NOT_TO_READ_ASSISTANT/AUDIENCE_GUIDE.md`](NOT_TO_READ_ASSISTANT/AUDIENCE_GUIDE.md)
- Product backlog and epic status: [`NOT_TO_READ_ASSISTANT/PRODUCT_BACKLOG.md`](NOT_TO_READ_ASSISTANT/PRODUCT_BACKLOG.md)
- Agent architecture and runtime details: [`agentic_system/README.md`](agentic_system/README.md)
- Developer tools and skill progression: [`dev_tools/README.md`](dev_tools/README.md)
- Infrastructure and service-level details: [`db/README.md`](db/README.md)

## Documentation (`NOT_TO_READ_ASSISTANT/docs/`)

| Document | Purpose |
|----------|---------|
| [`NOT_TO_READ_ASSISTANT/docs/PRESENTER_GUIDE.md`](NOT_TO_READ_ASSISTANT/docs/PRESENTER_GUIDE.md) | Presenter guide — timing, commands, and talking points for all three phases |
| [`NOT_TO_READ_ASSISTANT/docs/ARCHITECTURE.md`](NOT_TO_READ_ASSISTANT/docs/ARCHITECTURE.md) | AgentAsTools data flow, file map, technology choices |
| [`NOT_TO_READ_ASSISTANT/docs/DEV_TOOLS.md`](NOT_TO_READ_ASSISTANT/docs/DEV_TOOLS.md) | Skill progression guide (00_naive → 03_fully_guided) and schema_sync reference |
| [`NOT_TO_READ_ASSISTANT/docs/SCHEMA_REFERENCE.md`](NOT_TO_READ_ASSISTANT/docs/SCHEMA_REFERENCE.md) | GitHub Archive field definitions, pre/post migration schema, ghost contributor query |
| [`NOT_TO_READ_ASSISTANT/docs/TROUBLESHOOTING.md`](NOT_TO_READ_ASSISTANT/docs/TROUBLESHOOTING.md) | Common issues with infrastructure, TUI, migration, and tests |
