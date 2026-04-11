---
id: IMP-05
name: LOCAL_SEED Agent Mode — Config, Demo Routing, TUI Hints, Prompt Overrides
epic: Epic 8 - Improvements
status: [x] Done
summary: Add LOCAL_SEED env flag that routes the demo question, TUI hints, and agent prompt context to match the 18-row local dataset.
---

# IMP-05 - LOCAL_SEED Agent Mode — Config, Demo Routing, TUI Hints, Prompt Overrides

- Epic: Epic 8 - Improvements
- Priority: P1
- Estimate: M
- Status: [x] Done
- Source: PRODUCT_BACKLOG.md

## Objective

Introduce a `LOCAL_SEED` environment flag that, when set to `true`, routes the demo CLI question, TUI welcome hint, and both agent system prompts to the 18-row local dataset — preventing the agent from pivoting to `civicrm/civicrm-core` or applying bot filters that would produce misleading results.

## Description

The NL2SQL system prompt contains dataset facts (5M rows, 2011–2022 date range) and an explicit rule to pivot to `civicrm/civicrm-core` when the requested repo is not found. Without overriding these, the agent would either dismiss `org/repo-alpha`, `org/repo-beta`, and `org/repo-gamma` as absent from the dataset, or apply bot filters (`actor_login NOT LIKE '%[bot]%'`) that are unnecessary and noisy on the 18-row fixture.

The fix adds a runtime override block appended to the agent instructions at import time when `settings.local_seed = True`. This overrides the dataset facts and repo pivot rule without modifying the `.md` prompt files — which are also consumed by `schema_sync` and the upgrade gate test.

## Scope

- `agentic_system/config.py`: add `local_seed: bool = False` Pydantic settings field reading `LOCAL_SEED` env var.
- `agentic_system/demo.py`: add `LOCAL_DEMO_QUESTION` constant targeting the three local repos; `__main__` selects question based on `settings.local_seed`.
- `agentic_system/tui/app.py`: update welcome hint text and input placeholder conditionally on `settings.local_seed`.
- `agentic_system/agents_core/nl2sql/agent.py`: append `LOCAL SEED OVERRIDE` block to `_instructions` when `settings.local_seed` is `True`. Override covers: correct repos, row count, date range, ghost/regular contributor lists, no-pivot rule, no-bot-filter rule.
- `agentic_system/agents_core/rag/agent.py`: append matching `LOCAL SEED OVERRIDE` block with repo names and contributor facts.
- `.env.example`: add `LOCAL_SEED=false` with explanatory comment.

## Out Of Scope

- Modifying the `.md` prompt files (`system.md`, `examples.md`) — these must remain pre-migration for `schema_sync` and the upgrade gate to work correctly.
- Adding a CLI `--local` flag to `main.py` or `demo.py` (env var is sufficient for workshop use).
- Changing test fixtures or conftest.py (tests are mock-based and unaffected by `local_seed`).

## Deliverables

- `agentic_system/config.py` with `local_seed` field.
- `agentic_system/demo.py` with `LOCAL_DEMO_QUESTION` and routing.
- `agentic_system/tui/app.py` with conditional hints.
- `agentic_system/agents_core/nl2sql/agent.py` with override block.
- `agentic_system/agents_core/rag/agent.py` with override block.
- `.env.example` with `LOCAL_SEED=false`.

## Acceptance Criteria

- `settings.local_seed` is `True` when `LOCAL_SEED=true` or `LOCAL_SEED=1` is set in the environment.
- `python -m agentic_system.demo` with `LOCAL_SEED=true` asks about `org/repo-alpha`, `org/repo-beta`, `org/repo-gamma`.
- TUI welcome message and input placeholder reference local repos when `LOCAL_SEED=true`.
- Agent instructions tail (last ~300 chars) contains the LOCAL SEED OVERRIDE block when `LOCAL_SEED=true`.
- Standard CI test suite (16 tests) still passes — the override blocks are runtime-only and do not affect mocked tests.

## Dependencies

- IMP-01: local dataset must exist so the agent has something to query.
- IMP-02: `make seed LOCAL=1` must be functional so the data can be loaded.

## Assumptions

- Appending the override at the end of `_instructions` is sufficient for the LLM to weight it over the earlier dataset facts, given standard transformer attention patterns.
- A single `LOCAL_SEED` env var is the right granularity — no per-agent flags needed.

## Verification

Verified by:
1. Checking `settings.local_seed = True` with `LOCAL_SEED=1` in `.env`.
2. Confirming `agent_nl2sql.instructions[-300:]` contains the override text.
3. Running `uv run pytest -m "pre_migration or post_migration or schema_sync or complete_flow"` → 16 passed.

## Notes

- Completed 2026-04-09.
- The override is appended to `_instructions` at Python import time (module load), not per-request. Both agents are module-level singletons, so the override is stable for the session lifetime.
