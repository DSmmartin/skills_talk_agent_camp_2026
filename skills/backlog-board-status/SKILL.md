---
name: backlog-board-status
description: Fast status check for backlog tasks using `scripts/backlog_board.py` and `backlog/board.md`. Use when you need a compact view of task id, epic, status, and short description across sessions.
---

# Backlog Board Status

Use this skill to quickly inspect and refresh backlog status from task files.

## Purpose

- Keep `PRODUCT_BACKLOG.md` focused on scope and prioritization.
- Keep execution status centralized in `backlog/board.md`.
- Provide a fast, repeatable summary for session handoff.

## Required Tool

- `scripts/backlog_board.py`

## Workflow

1. Read current board:
   `python3 scripts/backlog_board.py`
2. Refresh board file after task updates:
   `python3 scripts/backlog_board.py --write-board`
3. Optional structured output:
   `python3 scripts/backlog_board.py --format json`

## Data Contract

The summary per task includes:

- `name`
- `epic`
- `status`
- `short description`

The script first checks YAML front matter fields (`id`, `name`, `epic`, `status`, `summary`) when present.
If front matter is missing, it falls back to parsing current markdown sections.

## Expected Outputs

- `backlog/board.md` with an updated task board table.
- Optional JSON summary for automation or quick filtering.
