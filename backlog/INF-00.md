---
id: INF-00
name: Epic 1 Setup
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Establish Epic 1 scope, baseline structure, and traceability before implementation tasks.
---

# INF-00 - Epic 1 Setup

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L604)

## Objective

Prepare Epic 1 so the infrastructure work starts from an agreed baseline. This task defines the scope, expected repository structure, and completion criteria for the infrastructure layer that supports the full demo.

## Description

Epic 1 is the foundation for the demo described in the product backlog:

- ClickHouse stores the GitHub Archive dataset slice.
- ChromaDB stores schema and Q&A context for RAG.
- MLflow captures tracing and observability for the agent workflow.
- Docker Compose wires the local stack together.
- Environment files and Make targets make the demo repeatable.

`INF-00` exists to formalize that setup before implementation tasks begin. It is a traceability task: it records what Epic 1 includes and what "ready" means for the first infrastructure pass.

## Scope

- Define the infrastructure components included in Epic 1.
- Define the repository areas expected for infrastructure work.
- Define the expected repository baseline for Epic 1 implementation.
- Define the acceptance criteria for the setup phase of Epic 1.
- Record dependencies and assumptions for later implementation tasks.

## Out Of Scope

- Building any Docker image.
- Writing the actual ClickHouse schema or seed scripts.
- Implementing ChromaDB or MLflow services.
- Creating the final `docker-compose.yml`.
- Running validation on macOS or Linux.
- Executing any infrastructure task.

## Deliverables

- A reviewed Epic 1 setup task file at `backlog/INF-00.md` with objective, scope, boundaries, acceptance criteria, dependencies, assumptions, and status.
- An updated Epic 1 backlog entry in `PRODUCT_BACKLOG.md` that tracks `INF-00`.
- A documented Epic 1 repository baseline covering:
  `db/clickhouse/`, `db/clickhouse/init/`, `db/clickhouse/config/`, `db/vectordb/`, `db/vectordb/init/`, `db/mlflow/`, `db/mlflow/init/`, `docker-compose.yml`, `.env.example`, and `Makefile`.

## Acceptance Criteria

- Epic 1 scope is documented and reviewable from one task file.
- The infrastructure components required by the demo are clearly listed.
- The expected repository structure is defined.
- The expected Epic 1 repository baseline is documented:
  `db/clickhouse/`, `db/clickhouse/init/`, `db/clickhouse/config/`, `db/vectordb/`, `db/vectordb/init/`, `db/mlflow/`, `db/mlflow/init/`, `docker-compose.yml`, `.env.example`, and `Makefile`.
- Boundaries between setup work and implementation work are clear.
- The task status is tracked and can be updated over time.

## Dependencies

- Product narrative and architecture defined in `PRODUCT_BACKLOG.md`.
- Agreement that Epic 1 supports local-first demo execution with Docker.
- Agreement that this task is a planning and traceability artifact, not an implementation task.

## Assumptions

- The demo remains centered on local Docker services for ClickHouse, ChromaDB, and MLflow.
- Python project setup is handled separately from the infrastructure setup defined here.
- Nice-to-have cloud deployment work remains outside Epic 1.

## Notes

- Completed on 2026-04-07 after review and approval of the Epic 1 setup artifact.
- This task records planning and traceability only; it does not imply implementation of infrastructure items.
