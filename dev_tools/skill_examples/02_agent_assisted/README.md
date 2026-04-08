# 02 — Agent-Assisted Skill

The skill provides the four-layer context table and a six-step repair sequence. Claude knows exactly what to do in what order — but has to implement each step from scratch.

## What it adds over 01_structured

- Four-layer table: which system, which file, what breaks
- Six named steps with enough detail to execute independently
- ChromaDB API path, embedding algorithm note
- Rollback strategy

## What Claude still has to figure out

- Exact text replacement patterns for each file
- ChromaDB HTTP call details (headers, payload shape)
- The embedding algorithm implementation
- Whether all occurrences were caught

## What comes next

→ [`03_fully_guided/`](../03_fully_guided/) — exact commands, scripts, complete replacement list, validation
