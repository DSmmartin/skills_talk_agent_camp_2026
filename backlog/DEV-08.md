---
id: DEV-08
name: dev_tools/scripts/prompt_patch.py
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Patches the NL2SQL and RAG system prompt .md files to replace pre-migration field references (merged UInt8, merged = 1) with post-migration equivalents (merged_at IS NOT NULL). Returns a list of PromptChange records.
---

# DEV-08 — dev_tools/scripts/prompt_patch.py

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L159)

## Objective

Patch the NL2SQL and RAG agent system prompts so that after `make migrate`, the agents generate correct SQL (`merged_at IS NOT NULL` instead of `merged = 1`) and describe the schema correctly. This is the layer that directly determines whether the agent returns correct rows in Act 3.

## Description

`prompt_patch.patch(dry_run)` reads two prompt files:
- `agentic_system/agents_core/nl2sql/prompts/system.md`
- `agentic_system/agents_core/rag/prompts/system.md`

It applies a set of ordered regex replacement rules using `re.subn()`. The rules cover:
- Schema table row: `| merged | UInt8 | ... |` → `| merged_at | Nullable(DateTime) | ... |`
- Type annotation: `merged UInt8` → `merged_at Nullable(DateTime)`
- SQL predicates: `` `merged = 1` `` → `` `merged_at IS NOT NULL` `` and `` `merged = 0` `` → `` `merged_at IS NULL` ``
- Instruction text referencing old predicate usage
- Bold markers: `**1**` / `**0**` → `**non-NULL**` / `**NULL**`
- State labels: `(pre-migration)` → `(post-migration)`

Returns `PromptChange` records (one per modified file) with the count of replacements applied.

## Scope

- `dev_tools/scripts/prompt_patch.py`:
  - `PromptChange` dataclass: `file`, `replacements_applied`
  - `PROMPT_FILES: list[Path]` — the two files to patch
  - `_REPLACEMENTS: list[tuple[str, str]]` — ordered regex rules
  - `_apply_replacements(text) → (patched_text, count)`
  - `patch(dry_run) → list[PromptChange]`
  - `main()` CLI entry point

## Out Of Scope

- Patching `agents_core/nl2sql/prompts/examples.md` or `rag/prompts/examples.md` (few-shot SQL examples — handled separately if needed).
- ChromaDB content (DEV-06).
- YAML contract (DEV-07).

## Deliverables

- `dev_tools/scripts/prompt_patch.py`

## Acceptance Criteria

- After running `prompt_patch.py`, neither prompt file contains `merged = 1` or `merged UInt8`.
- Both prompt files contain `merged_at IS NOT NULL` and `Nullable(DateTime)` where appropriate.
- `--dry-run` reports replacement counts without writing files.
- Returns empty list (no-op) when no replacements are needed (idempotent).

## Dependencies

- AGT-01 / AGT-02: prompt files exist at the expected paths.
- MIG-01: `make migrate` must have run so the prompts reference the pre-migration field.

## Assumptions

- Regex patterns are sufficient for the demo migration scenario (`merged → merged_at`).
- The NL2SQL system prompt table row format is stable (pipe-delimited Markdown).
- Running the patch twice on an already-patched file is a safe no-op (idempotent).

## Verification

```bash
# Syntax check
uv run python -c "import ast; ast.parse(open('dev_tools/scripts/prompt_patch.py').read()); print('OK')"

# Dry run (after make migrate)
uv run python dev_tools/scripts/prompt_patch.py --dry-run

# Full patch
uv run python dev_tools/scripts/prompt_patch.py

# Confirm no stale references remain
grep -n "merged = 1\|merged UInt8" \
  agentic_system/agents_core/nl2sql/prompts/system.md \
  agentic_system/agents_core/rag/prompts/system.md \
  && echo "FAIL: stale references found" || echo "OK: no stale references"
```

Expected after full patch:
```
OK: no stale references
```

## Notes

- Completed 2026-04-08.
- Replacement rules are ordered: table rows → type annotations → SQL predicates → prose text → state labels.
- The NL2SQL prompt's `sum(merged)` aggregate pattern is also replaced with `countIf(isNotNull(merged_at))`.
- Idempotent: running on an already-patched file returns `[]` (zero changes).
