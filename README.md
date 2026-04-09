# Skills Talk AgentCamp 2026

This repository hosts a reference implementation for a skills-first agentic system.

## What This Is

- An agentic NL2SQL system built on ClickHouse, ChromaDB, and MLflow.
- A reproducible local infrastructure baseline for data, retrieval, and tracing.
- A concrete codebase to study skill-driven repair workflows.

## Project Areas

- Agentic system: `agentic_system/README.md`
- Infrastructure and services: `db/README.md`

## Quick Start

```bash
make up
make seed
make seed-vectors
uv run python agentic_system/main.py
```

## Notes

- For extended materials and internal references, see `NOT_TO_READ_ASSISTANT/`.
