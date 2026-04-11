---
id: AGT-04
name: agentic_system/schema/github_events.yaml — Machine-Readable Schema Definition
epic: Epic 2 - Agentic System (Act 1)
status: [x] Done
summary: Create the YAML schema definition file for github_events that agents and schema-sync reference as the authoritative field contract.
---

# AGT-04 - agentic_system/schema/github_events.yaml — Machine-Readable Schema Definition

- Epic: Epic 2 - Agentic System (Act 1)
- Priority: P0
- Estimate: S
- Status: [ ] Todo
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L630)

## Objective

Create the machine-readable YAML schema file for the `github_events` table so agents and `schema_sync` have a single authoritative source for field names and types.

## Description

`agentic_system/schema/github_events.yaml` is the contract between the live ClickHouse schema and the agentic system. AgentRAG and AgentNL2SQL load it to stay aligned with the current table definition. During Act 2, the file goes stale when the schema migrates (`merged UInt8` → `merged_at DateTime NULL`). In Act 3, `schema_sync` diffs the live schema against this file and patches it as step 3 of the sync procedure. The file must reflect the **pre-migration** schema at creation time.

## Scope

- Create `agentic_system/schema/github_events.yaml` with all relevant fields from the pre-migration `github_events` table.
- Include field name, ClickHouse type, and a short description for each field.
- Use the fields defined in the backlog: `event_type`, `action`, `actor_login`, `repo_name`, `created_at`, `merged`, `number`, `title`.
- Mark `merged` explicitly with its pre-migration type `UInt8` so drift detection in `validate_schema.py` and `schema_sync` can compare against it.

## Out Of Scope

- Post-migration schema (`merged_at DateTime NULL`) — that is the result of Act 2/Act 3.
- Agent code that reads the YAML file (handled in AGT-01, AGT-02).
- schema_sync patching logic (Epic 4).
- ClickHouse table creation DDL (INF-02).

## Deliverables

- `agentic_system/schema/github_events.yaml` — pre-migration schema definition with all relevant `github_events` fields.

## Acceptance Criteria

- File exists at `agentic_system/schema/github_events.yaml`.
- All fields used in the ghost-contributor queries are present: `event_type`, `action`, `actor_login`, `repo_name`, `created_at`, `merged`, `number`, `title`.
- `merged` is typed as `UInt8` with a description noting it is the subject of the demo migration.
- The YAML structure is parseable by `scripts/validate_schema.py` (Epic 3) and `dev_tools/schema_sync.py` (Epic 4).

## Dependencies

- INF-02: ClickHouse DDL is the source of truth for field names and types at creation time.

## Assumptions

- YAML format uses a top-level `table` key and a `columns` list, each entry having `name`, `type`, and `description` keys — consistent with what `validate_schema.py` and `schema_sync` will expect.
- The file starts in pre-migration state; Act 3 patching will update it in place.

## Notes

- This file is explicitly listed in the backlog as one of the four layers broken by the schema migration. Keep the format simple and diff-friendly.
