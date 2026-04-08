# 01 — Structured Skill

The skill now lists the key files and systems to inspect, but leaves the HOW to Claude.

## What it adds over 00_naive

- Lists the four files/systems to check (YAML, NL2SQL prompt, RAG prompt, ChromaDB)
- Tells Claude to read the live schema first
- Points to `validate_schema.py` for drift detection

## What Claude still has to figure out

- How to connect to ClickHouse and ChromaDB
- What exact text to replace in each file
- How to re-embed ChromaDB chunks after updating them
- Whether it got everything right

## What comes next

→ [`02_agent_assisted/`](../02_agent_assisted/) — give Claude the four-layer table and a step sequence
