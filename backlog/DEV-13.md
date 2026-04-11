---
id: DEV-13
name: dev_tools/README.md — Skill Progression Guide
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: README explaining the skill_examples/ progression from 00_naive to 03_fully_guided, documenting schema_sync.py usage, all script CLI flags, and the four layers that schema_sync patches.
---

# DEV-13 — dev_tools/README.md — Skill Progression Guide

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L164)

## Objective

Provide a single entry-point document that explains what `dev_tools/` contains, how to run the schema-sync procedure, and what story the `skill_examples/` progression tells. A presenter or developer reading this file should understand the Act 3 narrative in under two minutes.

## Description

`dev_tools/README.md` covers:

1. **Quick start** — the four commands a presenter needs (`make schema-sync`, `--dry-run`, `--rollback`, manual invocation).
2. **The four layers** — table mapping each layer to its file(s) and what breaks after migration.
3. **File map** — annotated directory tree of the whole `dev_tools/` package.
4. **skill_examples/ progression** — one section per example (00–03), each with a one-line description, run command, what it improves, and what is still missing.
5. **schema_sync.py reference** — argument descriptions and sample output showing the four-step report.
6. **Key message** — the Act 3 takeaway: schema migrations are predictable; `schema_sync` formalises the response.

## Scope

- `dev_tools/README.md` only.
- No new code.

## Out Of Scope

- Per-script API documentation (each script has a module-level docstring).
- Installation instructions (covered in the root README).

## Deliverables

- `dev_tools/README.md`

## Acceptance Criteria

- Contains the four-layers table with file paths, breakage description, and fix command.
- Contains the annotated file map covering all scripts and skill_examples.
- Contains the skill_examples progression with an improvement comparison for each step.
- Contains the `schema_sync.py --help` argument reference and sample terminal output.
- No broken relative links to the four `skill_examples/README.md` files.

## Dependencies

- DEV-01 through DEV-12: all artefacts described in the README must exist.

## Assumptions

- Rendered in GitHub-flavoured Markdown (tables, code blocks, relative links).
- Sample terminal output reflects the actual output of `schema_sync.py` after `make migrate`.

## Verification

```bash
# File exists
ls dev_tools/README.md

# All four skill_example READMEs linked exist
for d in 00_naive 01_structured 02_agent_assisted 03_fully_guided; do
  [ -f "dev_tools/skill_examples/$d/README.md" ] && echo "OK $d" || echo "MISSING $d"
done
```

## Notes

- Completed 2026-04-08.
- The "Key message" section is intentionally brief — it is the one sentence the presenter says aloud during Act 3.
