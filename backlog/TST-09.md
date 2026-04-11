---
id: TST-09
name: test_schema_sync.py — Unit Tests for Each Patch Utility Function
epic: Epic 5 - Tests
status: [x] Done
summary: Unit tests for yaml_patch.patch(), chroma_patch.patch(), and prompt_patch.patch() using fixture files and mock clients. Validates each layer's patching logic in isolation.
---

# TST-09 — test_schema_sync.py — Unit Tests for Each Patch Utility Function

- Epic: Epic 5 - Tests
- Priority: P1
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L187)

## Objective

Validate that each individual patch utility (`yaml_patch`, `chroma_patch`, `prompt_patch`) produces the correct output when given the pre-migration state — without relying on live services or the full `schema_sync` orchestrator.

## Description

Three test groups in `tests/test_schema_sync.py`:

**`test_yaml_patch`** — calls `yaml_patch.patch(table, live_cols, dry_run=False)` using fixture data from `tests/fixtures/`. Asserts that `merged_at` column is added to the YAML and the returned `YamlChange` list records the addition.

**`test_chroma_patch`** — calls `chroma_patch.patch(dry_run=False)` with a mock ChromaDB client that returns a stale chunk. Asserts the chunk document is updated (`merged UInt8 → merged_at Nullable(DateTime)`, `merged = 1 → merged_at IS NOT NULL`), re-embedded (different vector), and upserted.

**`test_prompt_patch`** — calls `prompt_patch.patch(dry_run=False)` with actual prompt files (or copies). Asserts both `system.md` files no longer contain `merged = 1` after patching, and the returned `PromptChange` list records the replacements.

Each test also verifies the `--dry-run` behaviour: `dry_run=True` returns the same change list but does not write any files or call ChromaDB upsert.

## Scope

- `tests/test_schema_sync.py` — three test groups for the three patch utilities.
- Uses `tests/fixtures/` files from TST-02 as input data.

## Out Of Scope

- The `schema_sync.sync()` orchestrator (tested end-to-end by TST-07/08).
- `clickhouse_introspect.py` (tested implicitly via TST-05; no separate unit test needed).

## Deliverables

- `tests/test_schema_sync.py` with three test groups: `test_yaml_patch`, `test_chroma_patch`, `test_prompt_patch`.
- Each group includes a dry-run variant.

## Acceptance Criteria

- `test_yaml_patch` asserts `merged_at` appears in the patched YAML and `YamlChange` list is non-empty.
- `test_chroma_patch` asserts chunk document no longer contains `merged = 1` and upsert was called.
- `test_prompt_patch` asserts both prompt files no longer contain `merged = 1` and `PromptChange` list is non-empty.
- All three dry-run variants assert no files were written and no ChromaDB calls were made.

## Dependencies

- TST-02: `tests/fixtures/` files for pre/post YAML snapshots.
- DEV-05..08: The actual patch utilities being tested.
- TST-01: Base fixtures reused where applicable.

## Assumptions

- Prompt patch tests operate on copies of the actual system prompt files (to avoid modifying the repo state during the test run).
- ChromaDB is fully mocked for `test_chroma_patch`.

## Verification

```bash
uv run pytest tests/test_schema_sync.py -v -k "test_yaml_patch or test_chroma_patch or test_prompt_patch"
```

Expected:
```
tests/test_schema_sync.py::test_yaml_patch PASSED
tests/test_schema_sync.py::test_yaml_patch_dry_run PASSED
tests/test_schema_sync.py::test_chroma_patch PASSED
tests/test_schema_sync.py::test_chroma_patch_dry_run PASSED
tests/test_schema_sync.py::test_prompt_patch PASSED
tests/test_schema_sync.py::test_prompt_patch_dry_run PASSED
```

## Notes

- These are the unit-level safety net. If TST-07 fails, these tests identify which layer is broken.
- The dry-run tests are critical: they validate that `--dry-run` truly touches nothing.
