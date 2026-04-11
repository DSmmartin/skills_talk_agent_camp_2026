---
id: TST-13
name: Schema Upgrade Gate — Explicit Post-Migration Readiness Check
epic: Epic 5 - Tests
status: [x] Done
summary: Pending suggestion. Add a strict gate test profile that must fail until repository code and prompts are fully upgraded for post-migration schema (`merged_at`).
---

# TST-13 - Schema Upgrade Gate — Explicit Post-Migration Readiness Check

- Epic: Epic 5 - Tests
- Priority: P2
- Estimate: S
- Status: [ ] Todo
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md)

## Objective

Track the pending suggestion as an explicit test contract: in post-migration mode, fail unless code files are fully upgraded for `merged_at` semantics.

## Description

This task formalizes a separate readiness gate (`schema_upgrade_gate`) that checks repository files directly (schema contract + prompt/tool text) and fails when legacy `merged = 1` guidance remains in places that should be upgraded.

This gate is intentionally **state-sensitive** and should run only in a post-migration verification profile, not as part of the default pre-migration baseline run.

## Scope

- `tests/test_schema_upgrade_gate.py`
- Marker usage policy in `tests/README.md`
- Optional CI profile split (`pre` vs `post_migration_upgrade`)

## Out Of Scope

- Rewriting migration strategy.
- Changing Act 1 pre-migration baseline behavior.

## Deliverables

- A documented and repeatable gate command for post-migration readiness.
- Clear failure reasons tied to files that still contain legacy guidance.

## Acceptance Criteria

- Gate fails on pre-migration baseline state.
- Gate passes after migration + schema sync + required file updates.
- Gate is not accidentally included in baseline CI profile.

## Dependencies

- TST-07, TST-08, TST-12.
- DEV-08 / DEV-09 patch workflows.

## Assumptions

- Team wants to keep both baseline and upgrade-gate profiles available.

## Verification

```bash
# Explicit gate profile (run only when validating post-migration readiness)
uv run pytest tests/test_schema_upgrade_gate.py -q
```

Expected verification result:

- Fails on baseline pre-migration repo state.
- Passes only when post-migration readiness is fully applied.

## Notes

- Deferred until documentation and audience guides are finalized.
