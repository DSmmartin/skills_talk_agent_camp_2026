---
id: INF-09
name: Verify Cold-Start on macOS (Apple Silicon)
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Validate cold-start from clean state on macOS Apple Silicon using the standard make workflow.
---

# INF-09 - Verify Cold-Start on macOS (Apple Silicon)

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L619)

## Objective

Validate that a clean infrastructure bootstraps reliably from zero state on macOS (Apple Silicon).

## Description

This task verifies the macOS execution path for Epic 1 using Apple Silicon only. The focus is a true cold-start path with the standardized commands established in `INF-08`, including stack startup and both seed flows.

The output is a macOS execution report that records timing, command outcomes, and issues so Epic 1 can be reviewed with concrete evidence.

## Scope

- Execute a full cold-start run on macOS (Apple Silicon).
- Use the standard command path:
  `make up && make seed && make seed-vectors`.
- Confirm core containers are healthy and reachable.
- Record elapsed time and any platform-specific deviations.
- Capture troubleshooting notes for failures and retest after fixes.

## Out Of Scope

- Implementing new platform-specific features unrelated to infra startup.
- Epic 2+ application behavior (agent orchestration, TUI, schema-sync).
- Cloud deployment validation.
- Performance benchmarking beyond cold-start completion time.

## Deliverables

- A macOS (Apple Silicon) cold-start verification report in this task file.
- Command transcript summary (pass/fail + timing) for macOS.
- Confirmed command baseline for Epic 1:
  `make up`, `make seed`, `make seed-vectors`, `make down`.
- A list of discovered platform issues with resolution notes (if any).

## Acceptance Criteria

- Cold-start completes on macOS (Apple Silicon) from clean state.
- `make up && make seed && make seed-vectors` succeeds without manual ad-hoc steps.
- ClickHouse, ChromaDB, and MLflow are running and reachable after startup.
- No blocking macOS-specific issue remains unresolved.
- Evidence is captured in this task file with commands and outcomes.

## Dependencies

- `INF-01` through `INF-08` completed.
- Docker + Docker Compose installed and functional on macOS (Apple Silicon).
- Network access to required seed data source for ClickHouse sample load.

## Assumptions

- The local macOS Apple Silicon host can run Docker containers with required resources.
- Port conflicts can be handled by existing setup behavior (MLflow fallback when needed).
- Validation operators have shell access to run `make` commands on each host.

## Verification

Procedure executed on macOS (Apple Silicon):

1. Start from clean state with `make reset`.
2. Run cold-start path with `make up`, `make seed`, and `make seed-vectors`.
3. Confirm service health using compose `ps`.
4. Validate runtime checks:
   ClickHouse row count and MLflow experiment availability.
5. Stop environment with `make down`.

Commands used:

```bash
make reset
make up
make seed
make seed-vectors
docker compose -p skills_talk_agent_camp_2026 -f docker-compose.yml ps
make down
```

Observed results:

- `make reset` succeeded and recreated volumes from clean state.
- `make up` succeeded; because host port `5000` was occupied, setup auto-selected fallback MLflow host port `5003`.
- `make seed` succeeded and loaded exactly `5,000,000` rows into `github_events`.
- `make seed-vectors` succeeded:
  `schema_docs` count `1`,
  `qa_examples` count `2`,
  and smoke query top matches were `qa_examples:ghost_contribs` and `qa_examples:unmerged_prs`.
- `docker compose ... ps` showed all three services in `Up` state.
- ClickHouse runtime check returned `5000000` rows.
- MLflow runtime check confirmed `ghost-contributors-demo` experiment exists (`ok`).
- `make down` succeeded and removed containers and network.

## Notes

- Created on 2026-04-07 as the next Epic 1 task after `INF-08`.
- Completed on 2026-04-07 on macOS Apple Silicon.
- Linux validation is split into `INF-10`.
