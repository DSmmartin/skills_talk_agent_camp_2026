---
id: DEV-01
name: skill_examples/00_naive/SKILL.md — Naive Skill
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Naive SKILL.md with no files listed and no procedure — just "something broke, fix it." Baseline for the skill progression that shows what happens when Claude has no guidance.
---

# DEV-01 — skill_examples/00_naive/SKILL.md — Naive Skill

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L152)

## Objective

Establish the baseline skill — the one a developer would write in 30 seconds when the PM says "the agent is broken, fix it." No files listed, no procedure, no context about the four layers. Claude is on its own.

## Description

`00_naive/SKILL.md` contains nine words of instruction:

> *"Something changed in the database and the agentic system is broken. Investigate the codebase and fix whatever is broken."*

This is the starting point of the progression. When this skill is invoked, Claude must explore the codebase from scratch, discover the four-layer architecture, find the stale references, and decide what to patch — all without guidance. The result is unpredictable: it might work, might miss ChromaDB, might fix prompts but forget the YAML contract.

The README explains exactly what happens (and what can go wrong), and links to `01_structured/` as the next step.

## Scope

- `dev_tools/skill_examples/00_naive/SKILL.md` — the skill procedure file (9 words of instruction).
- `dev_tools/skill_examples/00_naive/README.md` — explains what the skill does and doesn't do, and what happens when Claude uses it.

## Out Of Scope

- Any scripts or tooling (this skill level has none by design).
- ChromaDB, YAML, or prompt patching guidance.

## Deliverables

- `dev_tools/skill_examples/00_naive/SKILL.md`
- `dev_tools/skill_examples/00_naive/README.md`

## Acceptance Criteria

- `SKILL.md` has a valid frontmatter block (`name`, `description`).
- The body contains no file paths, no procedure, no layer references.
- README explains the likely failure modes and links to `01_structured/`.

## Dependencies

- MIG-01: `make migrate` sets up the broken state that this skill is meant to address.

## Assumptions

- The skill is intentionally sparse — that is the teaching artefact, not a deficiency to fix.
- Claude Code can discover and invoke the skill after it is installed.

## Verification

```bash
# Confirm SKILL.md exists and has frontmatter
head -5 dev_tools/skill_examples/00_naive/SKILL.md

# Confirm it has no file paths or procedure steps
grep -c "agentic_system\|Step\|patch\|uv run" dev_tools/skill_examples/00_naive/SKILL.md
# Expected: 0

# Confirm README exists and links to 01_structured
grep "01_structured" dev_tools/skill_examples/00_naive/README.md
```

Expected output:
```
---
name: schema-sync-naive
description: The database schema changed and the agent is returning wrong answers. Fix it.
---
0
../01_structured/
```

## Notes

- Completed 2026-04-08.
- The contrast with `03_fully_guided` is the point: same problem, 9 words vs. 80 lines.
- Skill progression: **00_naive** → 01_structured → 02_agent_assisted → 03_fully_guided.
