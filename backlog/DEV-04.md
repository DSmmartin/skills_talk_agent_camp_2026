---
id: DEV-04
name: skill_examples/03_fully_guided/SKILL.md — Fully Guided Skill
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Fully guided SKILL.md with one-command fix, step-by-step fallback with exact uv run commands, pre/post validation, rollback procedure, and a references/ directory with the full replacement list and embedding algorithm.
---

# DEV-04 — skill_examples/03_fully_guided/SKILL.md — Fully Guided Skill

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P1
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L155)

## Objective

Show the payoff of the skill progression: a fully guided procedure where Claude follows exact steps, runs validated tooling, and resolves the schema drift in a single command without exploration. This is the "best Skill" the demo asks for.

## Description

`03_fully_guided/SKILL.md` gives Claude everything it needs:

**One-command fix** — for the standard `merged → merged_at` migration:
```bash
uv run python dev_tools/schema_sync.py --table github_events --dry-run  # preview
uv run python dev_tools/schema_sync.py --table github_events             # apply
uv run python scripts/validate_schema.py                                  # confirm
```

**Step-by-step fallback** — for non-standard migrations, each layer has exact `uv run` commands for its patching script (with `--dry-run` preview), plus manual patching instructions with the complete replacement list.

**Pre-check / post-check** — explicit validation steps before and after.

**Rollback** — `uv run python dev_tools/schema_sync.py --table github_events --rollback` restores YAML and prompts from the pre-sync snapshot; `make seed-vectors` restores ChromaDB.

**References directory** — `references/schema-layers.md` contains:
- The demo migration table (`merged UInt8 → merged_at Nullable(DateTime)`)
- Layer-by-layer replacement lists (YAML entry, NL2SQL replacements, RAG replacements)
- The full 64-dimension deterministic hash embedding algorithm (identical to `seed_vectors.py`)
- Connection settings for ClickHouse and ChromaDB

The README contains the full four-column comparison table (naive vs fully guided) and explains the balance point.

## Scope

- `dev_tools/skill_examples/03_fully_guided/SKILL.md` — complete procedure with one-command fix, fallback steps, validation, and rollback.
- `dev_tools/skill_examples/03_fully_guided/references/schema-layers.md` — replacement list, embedding algorithm, connection settings.
- `dev_tools/skill_examples/03_fully_guided/README.md` — balance-point comparison table.

## Out Of Scope

- The actual patching logic (lives in `dev_tools/scripts/`).
- Any scripts written as part of the skill itself (`dev_tools/scripts/` is referenced, not duplicated).

## Deliverables

- `dev_tools/skill_examples/03_fully_guided/SKILL.md`
- `dev_tools/skill_examples/03_fully_guided/references/schema-layers.md`
- `dev_tools/skill_examples/03_fully_guided/README.md`

## Acceptance Criteria

- `SKILL.md` contains a one-command fix using `dev_tools/schema_sync.py`.
- Step-by-step fallback covers all four layers with exact `uv run python dev_tools/scripts/...` commands.
- Pre-check and post-check validation steps are present.
- Rollback procedure with exact commands is present.
- `references/schema-layers.md` exists and contains the embedding algorithm.
- README contains the four-column comparison table (Claude effort, token cost, reliability, generality, maintenance).

## Dependencies

- DEV-09: `dev_tools/schema_sync.py` is the one-command fix (must exist before the skill can reference it).
- DEV-05..08: individual patching scripts referenced in the fallback procedure.
- MIG-04: `scripts/validate_schema.py` referenced in pre/post checks.

## Assumptions

- Services (ClickHouse, ChromaDB) must be running when the skill is invoked.
- The skill is only valid for the `merged → merged_at` migration pattern; non-standard migrations use the step-by-step fallback.

## Verification

```bash
# Confirm one-command fix references schema_sync.py
grep "schema_sync.py" dev_tools/skill_examples/03_fully_guided/SKILL.md

# Confirm all four patching scripts are referenced in the fallback
grep -c "clickhouse_introspect\|yaml_patch\|chroma_patch\|prompt_patch" dev_tools/skill_examples/03_fully_guided/SKILL.md
# Expected: 4

# Confirm rollback is present
grep "rollback" dev_tools/skill_examples/03_fully_guided/SKILL.md

# Confirm references directory exists
ls dev_tools/skill_examples/03_fully_guided/references/

# Confirm embedding algorithm is in references
grep "deterministic\|sha256\|hashlib" dev_tools/skill_examples/03_fully_guided/references/schema-layers.md
```

Expected output:
```
uv run python dev_tools/schema_sync.py --table github_events --dry-run
4
uv run python dev_tools/schema_sync.py --table github_events --rollback
schema-layers.md
hashlib
```

## Notes

- Completed 2026-04-08.
- This is the "best Skill" the demo asks for — every future schema migration should extend this procedure rather than start from scratch.
- The `references/` subdirectory is the key differentiator: it gives Claude all the domain knowledge it would otherwise have to discover (embedding algorithm, API payloads, connection settings).
- Skill progression: 00_naive → 01_structured → 02_agent_assisted → **03_fully_guided**.
