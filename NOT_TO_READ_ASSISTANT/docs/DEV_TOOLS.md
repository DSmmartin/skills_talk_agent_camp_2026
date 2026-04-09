# Dev Tools — Skill Progression Guide

This guide explains the `dev_tools/` directory and the four-level skill quality progression in `dev_tools/skill_examples/`.

For quick-start commands, see `dev_tools/README.md`.

---

## The Core Question

After `make migrate` breaks the system silently, the PM says:

> *"The schema changed — fix the system."*

The workshop question is: **"Who can write the best Skill?"**

A **Skill** is a structured, reusable developer procedure written for Claude Code. The `skill_examples/` directory shows four answers to this question, each better than the last.

---

## The Four Layers That Break

One field rename (`merged UInt8` → `merged_at Nullable(DateTime)`) breaks four independent layers simultaneously:

| Layer | Location | What breaks |
|-------|----------|-------------|
| YAML schema contract | `agentic_system/schema/github_events.yaml` | `validate-schema` reports drift |
| ChromaDB RAG chunks | `schema_docs` + `qa_examples` collections | RAG retrieves stale `merged UInt8` context |
| NL2SQL system prompt | `agents_core/nl2sql/prompts/system.md` | Agent generates `merged = 1` → 0 rows |
| RAG system prompt | `agents_core/rag/prompts/system.md` | Agent describes wrong field semantics |

A repair is only complete when **all four** are fixed. Missing any one means the agent still fails (or fails differently).

---

## Skill Progression

### Level 00 — Naive (`skill_examples/00_naive/SKILL.md`)

```markdown
Something changed in the database and the agentic system is broken.
Investigate the codebase and fix whatever is broken.
```

**What Claude gets:** Nothing specific. No files, no steps, no validation.

**What happens:** Claude explores the codebase, reads files, reasons through the failure. It may find the root cause — or miss one of the four layers. Each run is unpredictable.

**Cost:** High token usage, high exploration time, inconsistent outcomes.

**Verdict:** Works sometimes. Expensive. Not repeatable.

---

### Level 01 — Structured (`skill_examples/01_structured/SKILL.md`)

Adds the list of affected layers and points to the validation script.

**What Claude gets:** The four file/system targets to inspect, plus `validate_schema.py` as the correctness check.

**Improvement:** Claude knows exactly where to look. No wasted exploration across unrelated files.

**Still missing:** What to replace, how to patch ChromaDB, how to rollback.

**Verdict:** Reliable detection. Repair is still ad-hoc — may miss ChromaDB or produce inconsistent prompt replacements.

---

### Level 02 — Agent-Assisted (`skill_examples/02_agent_assisted/SKILL.md`)

Adds a four-layer context table and an ordered six-step repair sequence.

**What Claude gets:** A structured procedure with clear ordering: introspect → YAML → ChromaDB → prompts → validate.

**Improvement:** The ordered workflow keeps repair steps coherent. Claude doesn't skip ChromaDB or patch prompts before updating the YAML.

**Still missing:** Exact replacement strings, one-command automation, robust rollback procedure.

**Verdict:** Reliable and coherent. Slower than necessary. Prompt replacements still require judgement calls.

---

### Level 03 — Fully Guided (`skill_examples/03_fully_guided/SKILL.md`)

Complete procedure: one command, exact replacements, pre/post validation, rollback.

**What Claude gets:** Everything it needs to fix the system deterministically without exploration or judgement calls.

Key additions over Level 02:
- One-command fix: `uv run python dev_tools/schema_sync.py --table github_events`
- Dry-run preview before writing changes
- Step-by-step fallback for non-standard migrations
- Exact replacement list for manual prompt editing
- Rollback procedure with exact commands
- Reference files for field mapping and embedding algorithm details

**Verdict:** Fast, deterministic, repeatable. This is what `schema_sync.py` implements.

---

## The Balance Point

The progression is not a recommendation to always write Level 03 skills. It is a spectrum:

| Level | Generalises to | Cost | Reliability |
|-------|---------------|------|-------------|
| 00 | Any codebase, any problem | Very high | Low |
| 01 | This system, any schema drift | Medium | Medium |
| 02 | This system, this migration pattern | Low | High |
| 03 | This system, this exact field rename | Very low | Very high |

**The right level** depends on how predictable the problem is. Schema migrations are predictable — the field rename was announced in a ticket. Level 03 is appropriate here. For an unknown production incident, start with Level 01.

---

## `schema_sync.py` — The Level 03 Tool

The fully guided skill calls `schema_sync.py`, which implements the four-step repair procedure as a CLI:

```bash
# Preview changes (nothing written)
uv run python dev_tools/schema_sync.py --table github_events --dry-run

# Apply all four patches
uv run python dev_tools/schema_sync.py --table github_events

# Rollback to pre-sync state
uv run python dev_tools/schema_sync.py --table github_events --rollback
```

Or via Makefile:

```bash
make schema-sync-dry
make schema-sync
```

### What `schema_sync.py` does

```
Step 1/4  ClickHouse introspect
  → reads live schema from ClickHouse, identifies drift vs YAML contract

Step 2/4  YAML contract patch
  → adds merged_at column entry, updates merged description

Step 3/4  ChromaDB chunk patch
  → finds stale chunks, applies text replacements, re-embeds

Step 4/4  Agent prompt patch
  → patches NL2SQL and RAG system prompt files

═══════════════════════════════════
  Schema Sync Report — github_events
  Total: 4 change(s) across all layers.
═══════════════════════════════════
```

---

## Individual Patch Scripts

Each step can also be run in isolation:

| Script | Purpose | CLI |
|--------|---------|-----|
| `scripts/clickhouse_introspect.py` | Read live ClickHouse schema for a table | `--table TABLE` |
| `scripts/yaml_patch.py` | Diff and update the YAML contract | `--table TABLE [--dry-run]` |
| `scripts/chroma_patch.py` | Find stale ChromaDB chunks and re-embed | `[--dry-run]` |
| `scripts/prompt_patch.py` | Patch NL2SQL and RAG system prompt files | `[--dry-run]` |

All scripts live in `dev_tools/scripts/`.

---

## `SchemaSyncReport`

Defined in `dev_tools/models.py`. Printed at the end of every `schema_sync` run.

Fields:
- `table` — ClickHouse table that was synced
- `timestamp` — UTC datetime of the sync
- `yaml_changes` — list of column additions and description updates
- `chroma_changes` — list of patched chunk IDs with replacement counts
- `prompt_changes` — list of patched prompt files with replacement counts
- `live_schema_snapshot` — dict of `{column: type}` at sync time

---

## Validation

After any repair, confirm the system is in sync:

```bash
uv run python scripts/validate_schema.py
# Expected: No drift — live schema matches YAML contract exactly.
```

Confirm the agent returns correct rows:

```bash
uv run python agentic_system/main.py
# Ask: "Show me repositories where users opened PRs but never got one merged"
# Expected: non-empty result set
```

Confirm prompts no longer reference the old predicate:

```bash
grep -r "merged = 1" agentic_system/agents_core/
# Expected: no output
```
