---
name: backlog-task-creator
description: Create or update `backlog/<TASK-ID>.md` task files for this repo using the established traceability format. Use when asked to add backlog task documents, standardize task scope and status, or derive task files from `PRODUCT_BACKLOG.md`.
---

# Backlog Task Creator

Create backlog task files that mirror the repo's planning format and keep task traceability explicit.

## Workflow

1. Read `PRODUCT_BACKLOG.md` to extract the task ID, story text, epic, priority, and estimate.
2. Read one or more existing files in `backlog/` to preserve the established local format.
3. Create or update `backlog/<TASK-ID>.md`.
4. Keep the file as a planning artifact unless the user explicitly asks to execute the task.

## Required Format

Use this structure:

- YAML front matter:
  - `id`
  - `name`
  - `epic`
  - `status`
  - `summary`
- Title: `# <TASK-ID> - <Task title>`
- Metadata bullets:
  - `Epic`
  - `Priority`
  - `Estimate`
  - `Status`
  - `Source`
- Sections:
  - `## Objective`
  - `## Description`
  - `## Scope`
  - `## Out Of Scope`
  - `## Deliverables`
  - `## Acceptance Criteria`
  - `## Dependencies`
  - `## Assumptions`
  - `## Verification`
  - `## Notes`

Read [references/task-template.md](references/task-template.md) before writing a new file.

## Formatting Rules

- Use the filename `backlog/<TASK-ID>.md`.
- Keep status in checkbox form: `[ ] Todo`, `[~] In Progress`, `[x] Done`.
- Default new tasks to `[ ] Todo` unless the user says otherwise.
- Keep YAML front matter and markdown metadata consistent.
- Keep content concise and task-specific.
- Write scope as implementation boundaries, not as a restatement of the whole epic.
- Keep `Out Of Scope` explicit so the task does not grow silently.
- Use `Deliverables` to state the concrete outputs the task should produce.
- Use `Source` to point back to `PRODUCT_BACKLOG.md`.
- Do not add a `Proposed Delivery Sequence` section.
- Do not claim work is implemented inside the task file unless the user explicitly asks to record completion.

## Task Framing

- Treat each file as a traceability artifact for planning and execution follow-up.
- Translate backlog story text into a concrete objective and acceptance criteria.
- Make the expected outputs explicit in `Deliverables`.
- Add dependencies only when they materially affect execution order or readiness.
- Keep assumptions short and defensible.

## Update Rules

- When updating an existing task file, preserve valid information already present.
- If the repo format changes, align older task files to the current format when asked.
- Keep terminology consistent with `PRODUCT_BACKLOG.md`.
