# Backlog Task Template

Use this template for new files in `backlog/`.

```md
---
id: <TASK-ID>
name: <Task title>
epic: <Epic name>
status: [ ] Todo
summary: <One-sentence short description>
---

# <TASK-ID> - <Task title>

- Epic: <Epic name>
- Priority: <Priority>
- Estimate: <Estimate>
- Status: [ ] Todo
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md)

## Objective

State the concrete outcome this task should achieve.

## Description

Summarize the task in repo-specific terms. Explain why it exists and what role it plays in the demo or system.

## Scope

- List the work included in the task.
- Keep each item concrete and verifiable.

## Out Of Scope

- List adjacent work that should not be included in this task.

## Deliverables

- List the concrete files, artifacts, behaviors, or outputs this task should produce.

## Acceptance Criteria

- Define the observable conditions that make the task complete.

## Dependencies

- List required prior tasks, files, or decisions only when relevant.

## Assumptions

- Record short assumptions that shape the task.

## Verification

Procedure used to verify the task after implementation:

1. Describe the verification steps.
2. Include the exact commands run.
3. Record the observed output.

```bash
# commands used
```

Expected verification result:

- Describe what a passing verification looks like.

## Notes

- Add review or execution notes when needed.
```

Rules:

- Do not add `Proposed Delivery Sequence`.
- Keep status as one of `[ ] Todo`, `[~] In Progress`, `[x] Done`.
- Keep YAML front matter aligned with markdown metadata.
- Keep the file focused on one backlog item only.
