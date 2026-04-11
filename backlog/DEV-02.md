---
id: DEV-02
name: skill_examples/01_structured/SKILL.md — Structured Skill
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Structured SKILL.md that lists the four files/systems to inspect and points to validate_schema.py. Claude knows where to look but still has to figure out the how.
---

# DEV-02 — skill_examples/01_structured/SKILL.md — Structured Skill

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L153)

## Objective

Show what a minimal-but-useful skill looks like: point Claude at the right files, tell it what to look for, and provide a validation command. Claude still has to discover the connection details, derive replacement rules, and handle ChromaDB re-embedding — but it won't waste time exploring unrelated parts of the codebase.

## Description

`01_structured/SKILL.md` names the four files and systems affected by a schema change:

1. `agentic_system/schema/github_events.yaml` — YAML schema contract
2. `agentic_system/agents_core/nl2sql/prompts/system.md` — NL2SQL prompt
3. `agentic_system/agents_core/rag/prompts/system.md` — RAG prompt
4. ChromaDB collections `schema_docs` and `qa_examples` — stale chunks

The skill tells Claude to read the live schema from ClickHouse first, look for old field names and SQL predicates, then update each file. It points to `scripts/validate_schema.py` as the verification step.

What Claude still has to figure out: connection settings, exact text replacements, ChromaDB API call shape, re-embedding algorithm.

The README explains the improvement over `00_naive` and links to `02_agent_assisted/`.

## Scope

- `dev_tools/skill_examples/01_structured/SKILL.md` — structured procedure file listing the four layers.
- `dev_tools/skill_examples/01_structured/README.md` — improvement table and next-step pointer.

## Out Of Scope

- Exact replacement rules (not provided at this skill level by design).
- ChromaDB API call details (left for Claude to discover).
- Any scripts or tooling.

## Deliverables

- `dev_tools/skill_examples/01_structured/SKILL.md`
- `dev_tools/skill_examples/01_structured/README.md`

## Acceptance Criteria

- `SKILL.md` names all four layers (YAML, NL2SQL prompt, RAG prompt, ChromaDB).
- The skill tells Claude to query ClickHouse for the live schema before making changes.
- `scripts/validate_schema.py` is referenced as the validation step.
- README explains what `01_structured` adds over `00_naive` and what Claude still has to figure out.

## Dependencies

- MIG-01: `make migrate` must have run so there is something to fix.
- MIG-04: `scripts/validate_schema.py` must exist (referenced in the skill).
- AGT-04: `agentic_system/schema/github_events.yaml` must exist.

## Assumptions

- Claude Code has access to ClickHouse and ChromaDB when the skill is invoked.
- The skill is intentionally incomplete — stopping short of connection details is the teaching point.

## Verification

```bash
# Confirm all four layers are mentioned
grep -c "github_events.yaml\|nl2sql.*system.md\|rag.*system.md\|ChromaDB" dev_tools/skill_examples/01_structured/SKILL.md
# Expected: 4

# Confirm validate_schema.py is referenced
grep "validate_schema" dev_tools/skill_examples/01_structured/SKILL.md

# Confirm README links to 02_agent_assisted
grep "02_agent_assisted" dev_tools/skill_examples/01_structured/README.md
```

Expected output:
```
4
python scripts/validate_schema.py
../02_agent_assisted/
```

## Notes

- Completed 2026-04-08.
- Key improvement over `00_naive`: Claude knows the four layers by name and has a validation command.
- Key gap vs `02_agent_assisted`: no step sequence, no connection details, no replacement guidance.
- Skill progression: 00_naive → **01_structured** → 02_agent_assisted → 03_fully_guided.
