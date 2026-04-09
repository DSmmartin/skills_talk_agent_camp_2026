# dev_tools — Schema Sync Developer Tools (Phase 3)

This directory contains the Phase 3 developer tools for the Ghost Contributors scenario.

After the Phase 2 schema migration (`make migrate`) renames `merged → merged_at`,
four layers of the agentic system break simultaneously. `schema_sync.py` patches
all four in one command.

---

## Baseline (Fallback)

Use this path to verify the environment and tooling, or as a live fallback.
For the primary flow, the goal is to create and iterate skills in `skill_examples/`.

```bash
# After running 'make migrate' and seeing wrong answers:
uv run python dev_tools/schema_sync.py --table github_events

# Preview without touching anything:
uv run python dev_tools/schema_sync.py --table github_events --dry-run

# Undo a previous sync:
uv run python dev_tools/schema_sync.py --table github_events --rollback

# Or via Makefile:
make schema-sync
make schema-sync-dry
```

---

## The four layers schema_sync patches

| Layer | File(s) | What breaks |
|-------|---------|-------------|
| YAML contract | `agentic_system/schema/github_events.yaml` | `validate-schema` reports drift |
| ChromaDB chunks | `schema_docs`, `qa_examples` collections | RAG returns stale `merged UInt8` context |
| NL2SQL prompt | `agentic_system/agents_core/nl2sql/prompts/system.md` | Agent generates `merged = 1` → 0 rows |
| RAG prompt | `agentic_system/agents_core/rag/prompts/system.md` | Agent describes wrong field semantics |

---

## File map

```
dev_tools/
├── schema_sync.py           # Main CLI — orchestrates all four steps
├── models.py                # SchemaSyncReport dataclass
├── scripts/
│   ├── clickhouse_introspect.py  # Step 1: read live schema from ClickHouse
│   ├── yaml_patch.py             # Step 2: update YAML contract
│   ├── chroma_patch.py           # Step 3: patch + re-embed stale RAG chunks
│   └── prompt_patch.py           # Step 4: patch NL2SQL + RAG prompt files
└── skill_examples/          # Procedure quality progression
    ├── 00_naive/            # Minimal instruction: "investigate and fix"
    ├── 01_structured/       # Lists the four layers to inspect
    ├── 02_agent_assisted/   # Adds context table + ordered repair steps
    └── 03_fully_guided/     # One-command flow + fallback + rollback
```

---

## The skill_examples/ progression

The `skill_examples/` directory tells the story of how a developer procedure
evolves from ad-hoc to fully automated. Each example builds on the previous one.

### [00_naive](skill_examples/00_naive/) — Minimal guidance

The skill contains only a short instruction ("something broke, fix it"), with no
file targets or ordered steps.

**Problems:** high exploration cost, easy to miss one of the four layers.

---

### [01_structured](skill_examples/01_structured/) — Layer-aware guidance

The skill names the four affected layers (YAML, NL2SQL prompt, RAG prompt,
ChromaDB chunks) and points to schema validation.

**Improvement:** Claude knows exactly where to inspect and in which systems drift appears.
**Still missing:** exact replacement rules, ChromaDB patch implementation details, rollback.

---

### [02_agent_assisted](skill_examples/02_agent_assisted/) — Guided repair flow

The skill adds a four-layer context table plus an ordered six-step procedure.

**Improvement:** ordered workflow reduces exploration and keeps repair steps coherent.
**Still missing:** one-command automation, exact replacement catalogue, robust rollback.

---

### [03_fully_guided](skill_examples/03_fully_guided/) — Fully guided procedure

All four layers, pre/post validation, rollback capability, SchemaSyncReport.
This is what `schema_sync.py` implements.

---

## schema_sync.py reference

```
usage: schema_sync.py [--table TABLE] [--dry-run] [--rollback]

Arguments:
  --table TABLE   ClickHouse table to sync (default: github_events)
  --dry-run       Show what would change, touch nothing
  --rollback      Reverse the most recent sync
```

### What it prints

```
── Step 1/4  ClickHouse introspect
  event_type     String
  ...
  merged_at      Nullable(DateTime)        ← new column

── Step 2/4  YAML contract patch
  yaml:added:merged_at (Nullable(DateTime))
  yaml:updated:merged (description refreshed for post-migration state)

── Step 3/4  ChromaDB chunk patch
  chroma:patched:schema_docs:pr_fields (8 replacement(s))

── Step 4/4  Agent prompt patch
  prompt:patched:agentic_system/agents_core/nl2sql/prompts/system.md (6 replacement(s))
  prompt:patched:agentic_system/agents_core/rag/prompts/system.md (1 replacement(s))

════════════════════════════════════════════════════
  Schema Sync Report — github_events
  2026-04-08 21:00:00 UTC
════════════════════════════════════════════════════
  Total: 4 change(s) across YAML contract, ChromaDB chunks, Agent prompts.
════════════════════════════════════════════════════
```

---

## Key message (Phase 3)

Schema migrations are **predictable**. `schema_sync` formalises the response as a
repeatable developer procedure. The next time a field is renamed, the fix is:

```bash
make migrate && uv run python dev_tools/schema_sync.py --table github_events
```

That's it.
