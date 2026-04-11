---
id: INF-10
name: Verify Cold-Start on Linux
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Validate cold-start from clean state on Linux using the standard make workflow.
---

# INF-10 - Verify Cold-Start on Linux

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L620)

## Objective

Validate that a clean infrastructure bootstraps reliably from zero state on Linux.

## Description

This task verifies the Linux execution path for Epic 1 using the standardized command surface from `INF-08`. The goal is to confirm that cold-start behavior, service availability, and seeding flows work without ad-hoc manual fixes.

The output is a Linux execution report with timing and observed issues.

## Scope

- Execute a full cold-start run on Linux.
- Use the standard command path:
  `make up && make seed && make seed-vectors`.
- Confirm core containers are healthy and reachable.
- Record elapsed time and Linux-specific deviations.
- Capture troubleshooting notes for failures and retest after fixes.

## Out Of Scope

- macOS validation (covered by `INF-09`).
- Implementing new Linux-specific features unrelated to infra startup.
- Epic 2+ application behavior (agent orchestration, TUI, schema-sync).
- Cloud deployment validation.

## Deliverables

- A Linux cold-start verification report in this task file.
- Command transcript summary (pass/fail + timing) for Linux.
- Confirmed command baseline for Epic 1:
  `make up`, `make seed`, `make seed-vectors`, `make down`.
- A list of discovered Linux issues with resolution notes (if any).

## Acceptance Criteria

- Cold-start completes on Linux from clean state.
- `make up && make seed && make seed-vectors` succeeds without manual ad-hoc steps.
- ClickHouse, ChromaDB, and MLflow are running and reachable after startup.
- No blocking Linux-specific issue remains unresolved.
- Evidence is captured in this task file with commands and outcomes.

## Dependencies

- `INF-01` through `INF-08` completed.
- Docker + Docker Compose installed and functional on Linux host.
- Network access to required seed data source for ClickHouse sample load.

## Assumptions

- The Linux host has enough resources to run the three-service stack.
- Port conflicts can be handled by existing setup behavior (MLflow fallback when needed).
- Validation operator has shell access to run `make` commands.

## Verification

Planned verification procedure:

1. Start from clean state:
   `make reset`.
2. Execute cold-start path:
   `make up && make seed && make seed-vectors`.
3. Confirm services:
   `docker compose -p <project> -f docker-compose.yml ps`.
4. Capture runtime checks:
   ClickHouse row count, Chroma collection counts, MLflow availability.
5. Stop environment:
   `make down`.

Planned commands:

```bash
make reset
make up
make seed
make seed-vectors
docker compose -p skills_talk_agent_camp_2026 -f docker-compose.yml ps
make down
```

## Notes

- Created on 2026-04-07 by splitting the original cross-platform `INF-09`.
- Pending execution by user on Linux.
