# Tests Guide

This folder contains the Epic 5 test suite for the Ghost Contributors scenario.

## Goals

- Protect the **pre-migration baseline** (Phase 1).
- Verify the **silent failure** after migration (Phase 2).
- Verify **schema-sync recovery** (Phase 3).
- Provide a mocked complete flow for fast regression checks.

## Markers

- `pre_migration`: baseline behavior with `merged` semantics.
- `post_migration`: broken behavior after migration (`merged = 1` returns 0 rows).
- `schema_sync`: patch/recovery contract tests.
- `complete_flow`: stateful mocked flow (pre -> post -> sync -> fixed).
- `schema_upgrade_gate`: strict post-migration readiness gate (pending suggestion profile).

## Recommended Commands

```bash
# Baseline (Phase 1)
uv run pytest -m pre_migration --tb=short -q

# Broken state checks (Phase 2)
uv run pytest -m post_migration --tb=short -q

# Recovery checks (Phase 3)
uv run pytest -m schema_sync --tb=short -q

# Mocked full lifecycle for kubernetes question
make test-complete-flow

# Full mock suite used in CI
uv run pytest -m "pre_migration or post_migration or schema_sync or complete_flow" --tb=short -q
```

## Live Verification Sequence

Use this when you want the real migrate/sync sequence on local infra:

```bash
make verify-complete-flow
```

This runs:
1. pre-migration tests
2. `make migrate`
3. post-migration tests
4. `schema_sync`
5. recovery tests
6. rollback cleanup

## Pending Suggestion: Upgrade Gate

`tests/test_schema_upgrade_gate.py` is a strict gate for full post-migration code readiness.

Run explicitly:

```bash
uv run pytest tests/test_schema_upgrade_gate.py -q
```

Important:
- It is expected to fail on normalized pre-migration repo state.
- Keep it as a separate profile until documentation flow is finalized.

## Notes

- Most tests are mock-first and do not require live ClickHouse/Chroma/OpenAI.
- Temporary directories under `tests/.tmp_*` are runtime artifacts and can be removed safely.
