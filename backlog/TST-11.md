---
id: TST-11
name: CI — pytest GitHub Actions Workflow
epic: Epic 5 - Tests
status: [x] Done
summary: GitHub Actions workflow running `pytest -m "pre_migration or post_migration or schema_sync or complete_flow"` without live DB or LLM. Validates test suite on every push to main or epic branches.
---

# TST-11 — CI — pytest GitHub Actions Workflow

- Epic: Epic 5 - Tests
- Priority: P1
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L189)

## Objective

Ensure that the full mock-based test suite runs automatically on every push — catching regressions in the agentic system, schema_sync tooling, and patch utilities without requiring live ClickHouse, ChromaDB, or OpenAI.

## Description

A single GitHub Actions workflow file (`.github/workflows/test.yml`) runs:

```bash
uv run pytest -m "pre_migration or post_migration or schema_sync or complete_flow" --tb=short -q
```

The workflow:
- Triggers on `push` to `main` and any branch matching `epic*`.
- Uses `ubuntu-latest` with Python 3.14 managed by `uv`.
- Installs dependencies with `uv sync`.
- Does NOT start Docker services (all external calls are mocked).
- Sets a minimal `OPENAI_API_KEY=test` env var to satisfy import-time validation in `agentic_system/config.py`.

The suite is mock-first and does not require Docker services in CI. `schema_sync` and `complete_flow` tests use isolated temporary files/mocks to avoid mutating repository state during the workflow run.

## Scope

- `.github/workflows/test.yml` — single workflow file.
- Optional: `conftest.py` update for a `CI_MODE` env flag that auto-selects mock clients.

## Out Of Scope

- Docker service provisioning in CI (no live services).
- End-to-end TUI testing.
- Performance or load testing.

## Deliverables

- `.github/workflows/test.yml`

## Acceptance Criteria

- Workflow triggers on push to `main` and `epic*` branches.
- `pytest -m "pre_migration or post_migration or schema_sync or complete_flow"` passes without any environment setup beyond `OPENAI_API_KEY=test`.
- Workflow status badge can be added to `README.md`.
- Total CI run completes in under 2 minutes.

## Dependencies

- TST-01..12: All test files must exist and pass locally before CI is configured.
- INF-08: `.env.example` defines the env vars CI needs to set.

## Assumptions

- `uv` is available in the GitHub Actions runner via `astral-sh/setup-uv` action.
- No secrets beyond a test-value `OPENAI_API_KEY` are needed for the mock-based test suite.

## Verification

```bash
# Local simulation of CI command
uv run pytest -m "pre_migration or post_migration or schema_sync or complete_flow" --tb=short -q

# After PR is merged, check Actions tab:
gh run list --workflow=test.yml --limit=5
```

Expected CI output:
```
................
16 passed in X.XXs
```

## Notes

- CI run remains mock-first and does not require Docker services.
- `complete_flow` tests are included in the same marker expression for end-to-end regression coverage.
