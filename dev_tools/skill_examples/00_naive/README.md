# 00 — Naive Skill

A skill with almost no guidance. Claude is told something is broken and must figure out the rest.

## SKILL.md content

```
The database schema changed and the agent is returning wrong answers. Fix it.
```

That's it. No files listed, no procedure, no context about the four layers.

## What happens when you use it

Claude explores the codebase from scratch. It might:
- Find the YAML contract (or might not)
- Notice the ChromaDB chunks (or miss them)
- Fix the prompts but forget to re-embed
- Take many exploration steps, use many tokens

**Result:** might work eventually, but unpredictable and expensive. Misses layers.

## What comes next

→ [`01_structured/`](../01_structured/) — at least tell Claude where to look
