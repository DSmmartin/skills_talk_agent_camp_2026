---
id: DEV-03
name: skill_examples/02_agent_assisted/SKILL.md — Agent-Assisted Skill
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Agent-assisted SKILL.md with a four-layer context table and a six-step repair sequence. Claude knows what to do and in what order — but still has to implement each step from the instructions.
---

# DEV-03 — skill_examples/02_agent_assisted/SKILL.md — Agent-Assisted Skill

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P1
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L154)

## Objective

Show how a skill with a structured context table and an ordered repair sequence dramatically reduces exploration cost and improves reliability — even when exact replacement values are not provided.

## Description

`02_agent_assisted/SKILL.md` provides the four-layer context table and a six-step procedure:

**Context table** — maps each layer to its file/system and what breaks:

| Layer | File / System | What breaks |
|-------|--------------|-------------|
| YAML contract | `agentic_system/schema/github_events.yaml` | Contract no longer matches live DB |
| NL2SQL prompt | `agents_core/nl2sql/prompts/system.md` | Old SQL predicates → 0 rows silently |
| RAG prompt | `agents_core/rag/prompts/system.md` | Wrong field semantics in answers |
| ChromaDB chunks | `schema_docs`, `qa_examples` | Stale context retrieved by RAG |

**Repair sequence**:
1. Introspect live schema from ClickHouse
2. Diff against YAML contract
3. Patch YAML contract
4. Patch agent prompts
5. Patch ChromaDB chunks (includes API path and re-embedding note)
6. Validate with `scripts/validate_schema.py`

The skill includes the ChromaDB API base path, notes the deterministic embedding requirement, and provides a rollback note. What Claude still has to figure out: exact text to replace per file, ChromaDB payload shape, the embedding function implementation.

The README explains the improvement over `01_structured` and links to `03_fully_guided/`.

## Scope

- `dev_tools/skill_examples/02_agent_assisted/SKILL.md` — four-layer table and six-step procedure.
- `dev_tools/skill_examples/02_agent_assisted/README.md` — improvement table and next-step pointer.

## Out Of Scope

- Exact `{old, new}` replacement pairs per file (provided in `03_fully_guided`).
- The `uv run` commands for each patching script.
- A `/references` directory (added in `03_fully_guided`).

## Deliverables

- `dev_tools/skill_examples/02_agent_assisted/SKILL.md`
- `dev_tools/skill_examples/02_agent_assisted/README.md`

## Acceptance Criteria

- `SKILL.md` contains the four-layer context table.
- Six numbered steps are present in the correct order.
- ChromaDB API path is included in step 5.
- The skill notes that re-embedding must use the deterministic hash algorithm.
- `scripts/validate_schema.py` is cited in step 6.
- README lists what this level adds over `01_structured` and what Claude still has to figure out.

## Dependencies

- MIG-01: `make migrate` must have run.
- MIG-04: `scripts/validate_schema.py` must exist.
- AGT-04: `agentic_system/schema/github_events.yaml` must exist.
- INF-04: ChromaDB must be running when the skill is invoked.

## Assumptions

- The six-step sequence covers the full repair in the correct dependency order.
- Providing the API path but not the full payload is intentional — it is the teaching gap at this level.

## Verification

```bash
# Confirm context table is present
grep -c "YAML contract\|NL2SQL prompt\|RAG prompt\|ChromaDB" dev_tools/skill_examples/02_agent_assisted/SKILL.md
# Expected: 4

# Confirm six steps are present
grep -c "^### Step" dev_tools/skill_examples/02_agent_assisted/SKILL.md
# Expected: 6

# Confirm validate step is present
grep "validate_schema" dev_tools/skill_examples/02_agent_assisted/SKILL.md

# Confirm README links to 03_fully_guided
grep "03_fully_guided" dev_tools/skill_examples/02_agent_assisted/README.md
```

Expected output:
```
4
6
uv run python scripts/validate_schema.py
../03_fully_guided/
```

## Notes

- Completed 2026-04-08.
- Key improvement over `01_structured`: structured step sequence eliminates exploration cost.
- Key gap vs `03_fully_guided`: no exact replacements, no `uv run` commands for scripts, no `references/`.
- Skill progression: 00_naive → 01_structured → **02_agent_assisted** → 03_fully_guided.
