# Demo Script — Ghost Contributors: Building Resilient Agentic Systems with Skills

**Duration:** ~20 minutes (5 + 3 + 7 + 5 buffer)
**Audience:** Developers and AI practitioners at AgentCamp 2026

---

## Pre-Demo Checklist

Run these before going on stage. All should complete without errors.

```bash
# 1. Start infrastructure
make up

# 2. Seed data (only needed on first run or after reset)
make seed
make seed-vectors

# 3. Validate baseline
uv run python scripts/validate_schema.py
# Expected: "No drift — live schema matches YAML contract exactly."

# 4. Launch TUI in a dedicated terminal
uv run python agentic_system/main.py

# 5. Open MLflow in browser
open http://localhost:5002
```

Have two terminals ready:
- **Terminal A** — running the TUI (`python agentic_system/main.py`)
- **Terminal B** — for migration and schema-sync commands

---

## Act 1 — It Works (~5 min)

**Message:** Multi-agent systems can answer sophisticated questions about real data.

### Setup (say this)

> "We have a GitHub Archive dataset — about 5 million pull request events. I want to find 'ghost contributors': developers who opened PRs on a repository but never got one merged."
>
> "The system is a two-agent NL2SQL pipeline. There's a RAG agent that retrieves schema context from ChromaDB, and an NL2SQL agent that generates ClickHouse SQL and executes it."

### Demo step 1 — Ask the question

In Terminal A (TUI), type:

```
Show me repositories where users opened PRs but never got one merged — the ghost contributors
```

**While the agent runs, narrate:**

> "Watch the trace panel on the right. The orchestrator first calls AgentRAG to pull schema context — it retrieves the field definitions for `merged`, `actor_login`, `repo_name`. Then it calls AgentNL2SQL with both the question and that context."

**After results appear:**

> "We get real rows. Repositories with ghost contributors — users who invested time, opened PRs, but never had one accepted."

### Demo step 2 — Conversation memory

Type a follow-up without re-specifying context:

```
Which of those repositories has the most ghost contributors?
```

> "Notice I didn't re-specify what a ghost contributor is. The system carries full conversation memory — every prior turn is part of the next agent call."

### Demo step 3 — MLflow trace (optional, ~1 min)

Switch to the browser (MLflow at localhost:5002).

> "MLflow captures every LLM call automatically. Here's the root run for this query, and nested beneath it — the AgentRAG span and AgentNL2SQL span. Token counts, latency, the exact SQL generated."

---

## Act 2 — It Breaks (~3 min)

**Message:** Schema migrations break agentic systems in ways that are silent and hard to diagnose.

### Setup (say this)

> "Now I'm going to simulate something that happens in every production system: a schema migration. The DBA renames the `merged` field to `merged_at` — a DateTime instead of a UInt8 flag. Better semantics, same data."
>
> "How many things break?"

### Demo step — Run migration

In **Terminal B**:

```bash
make migrate
```

Output will show columns being altered. Then go back to **Terminal A** (TUI) and ask the same question:

```
Show me repositories where users opened PRs but never got one merged
```

> "Zero rows. No error. No exception. The system returned a valid, empty result."

Pause for effect.

> "This is the worst kind of failure. The system is confident. It's just wrong."

**Why it breaks (say this):**

> "Four things broke simultaneously when one field was renamed:"
>
> "1. The NL2SQL prompt still says `merged = 1` — which now matches nothing in ClickHouse."
> "2. The RAG prompt describes `merged` as a UInt8 flag — wrong field semantics."
> "3. The YAML schema contract still lists `merged`, not `merged_at`."
> "4. The ChromaDB chunks still contain the old field description."
>
> "Four layers. One rename. And none of them raised an exception."

---

## Act 3 — It Heals (~7 min)

**Message:** Skills transform a one-off fix into a repeatable procedure.

### Part A — The skill progression (~4 min)

> "Before I show the fix, I want to show you how we got there."

Open `dev_tools/skill_examples/` in your editor or file browser. Walk through each level:

**00_naive:**
> "If I just tell Claude: 'something broke, fix it' — what happens? It explores. It reads files. It figures things out eventually. But it might miss one of the four layers. Expensive, unreliable."

**01_structured:**
> "If I name the four layers — YAML, NL2SQL prompt, RAG prompt, ChromaDB — Claude knows exactly where to look. Much better. But I still haven't told it what to replace or how to validate."

**02_agent_assisted:**
> "Now I add an ordered six-step procedure. Claude has a sequence to follow. It's coherent and repeatable. But the ChromaDB patch is still manual, and there's no rollback."

**03_fully_guided:**
> "This is the fully guided skill: one command, exact replacements documented, pre/post validation, rollback. When we formalised this procedure completely, we turned it into a tool."

### Part B — Run schema-sync (~3 min)

In **Terminal B**:

```bash
# Preview what will change
make schema-sync-dry
```

> "Dry-run shows every change before touching anything. YAML contract will get `merged_at` added. Two prompt files patched. ChromaDB chunk re-embedded."

```bash
# Apply
make schema-sync
```

> "The SchemaSyncReport tells us exactly what changed: YAML, ChromaDB, NL2SQL prompt, RAG prompt — all four layers in one pass."

Go back to **Terminal A** (TUI):

```
Show me repositories where users opened PRs but never got one merged
```

> "Correct rows. Same question, same agent, repaired system."

### Closing message

> "Schema migrations are predictable. The field rename was announced in a ticket. The fix is known. What's new here is that we formalised it."
>
> "The Skill is the unit of that formalisation. From 'investigate and fix' to 'one command'. The quality of the Skill determines how reliably the agent performs the repair."
>
> "`make migrate && make schema-sync`. That's the full Act 2 + Act 3 in two commands."

---

## Teardown (after the session)

```bash
make down
# or to fully reset volumes:
make reset
```

---

## Timing Summary

| Act | Content | Target time |
|-----|---------|-------------|
| Pre-demo setup | Infrastructure check, TUI launch | Before stage |
| Act 1 | Ghost contributor query + memory demo | 5 min |
| Act 2 | Migration + silent failure | 3 min |
| Act 3 | Skill progression + schema-sync fix | 7 min |
| Q&A buffer | — | 5 min |

---

## Fallback Options

**If the TUI doesn't launch:** use `agentic_system/demo.py` directly:

```bash
uv run python agentic_system/demo.py
```

**If ChromaDB is unreachable:** restart the stack:

```bash
make down && make up
```

**If schema-sync fails:** run steps individually:

```bash
uv run python dev_tools/scripts/clickhouse_introspect.py --table github_events
uv run python dev_tools/scripts/yaml_patch.py --table github_events
uv run python dev_tools/scripts/chroma_patch.py
uv run python dev_tools/scripts/prompt_patch.py
```

**To restore the pre-migration state at any point:**

```bash
make rollback
```
