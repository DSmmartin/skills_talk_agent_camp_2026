# AgentCamp 2026 — Workshop Guide

## Ghost Contributors: Building Resilient Agentic Systems with Skills

**Workshop format:** Live demo + hands-on  
**Repository:** `skills-talk-agent-camp-2026`  
**Recommended branch for audience-facing materials:** `workshop-mode`

---

## Table of Contents

1. [What You Will Learn](#1-what-you-will-learn)
2. [Requirements](#2-requirements)
3. [Getting the Repository](#3-getting-the-repository)
4. [Configuration](#4-configuration)
5. [Infrastructure Setup](#5-infrastructure-setup)
6. [High-Level Architecture](#6-high-level-architecture)
7. [The Use Case — Ghost Contributors](#7-the-use-case--ghost-contributors)
8. [The Three-Act Demo](#8-the-three-act-demo)
   - [Act 1 — It Works](#act-1--it-works)
   - [Act 2 — It Breaks](#act-2--it-breaks)
   - [Act 3 — It Heals](#act-3--it-heals)
9. [Skills — The Core Concept](#9-skills--the-core-concept)
10. [Running the Tests](#10-running-the-tests)
11. [Observability](#11-observability)
12. [Teardown](#12-teardown)
13. [Reference — All Commands](#13-reference--all-commands)

---

## 1. What You Will Learn

This workshop demonstrates how **Skills** — structured, reusable developer procedures — transform agentic systems from fragile demos into production-ready workflows.

By the end you will have seen:

- A working multi-agent NL2SQL system that answers natural language questions about GitHub activity.
- How a real schema migration silently breaks the system across **four independent layers** at once.
- How formalising a Skill leads naturally to `make schema-sync` — a single command that repairs all four layers.
- How the **quality of a Skill** — from naive to fully guided — directly determines how reliably Claude performs the repair.

---

## 2. Requirements

The following tools must be installed on your machine before the workshop:

| Tool | Purpose | Install guide |
|------|---------|---------------|
| [Git](https://git-scm.com/downloads) | Clone and manage the repository | git-scm.com/downloads |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2) | Run ClickHouse, ChromaDB, and MLflow locally | docker.com/products/docker-desktop |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Python package and environment manager | docs.astral.sh/uv |
| [Make](https://www.gnu.org/software/make/) | Task runner for workshop commands | Pre-installed on macOS/Linux; Windows: via [Chocolatey](https://chocolatey.org/) or WSL |

**Python version:** The project targets Python **3.14+**. `uv` manages this automatically — no manual Python install needed.

**OpenAI API access:** You need either an [OpenAI API key](https://platform.openai.com/api-keys) or an [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) deployment to run the live agent.

> Tests run fully offline with mocks — no API key is needed for the test suite.

---

## 3. Getting the Repository

```bash
git clone https://github.com/DSmmartin/skills_talk_agent_camp_2026.git
cd skills_talk_agent_camp_2026
git checkout workshop-mode
```

Install Python dependencies:

```bash
uv sync
```

---

## 4. Configuration

Copy the environment template and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` and set your OpenAI provider:

```bash
# For OpenAI
OPENAI_PROVIDER=openai
OPENAI_API_KEY=sk-...

# For Azure OpenAI
OPENAI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-azure-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

All other values have working defaults and can be left as-is for local development.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4o` | Model name (or Azure deployment name) |
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `CLICKHOUSE_HOST` | `localhost` | ClickHouse HTTP host |
| `CLICKHOUSE_PORT` | `8123` | ClickHouse HTTP port |
| `MLFLOW_TRACKING_URI` | `http://localhost:5002` | MLflow tracking server |
| `MLFLOW_EXPERIMENT_NAME` | `ghost-contributors` | MLflow experiment name |

---

## 5. Infrastructure Setup

Start all three services, seed the databases, and verify everything is running:

```bash
# Start ClickHouse, ChromaDB, and MLflow
make up

# Seed ClickHouse with ~5 million GitHub Archive pull-request events
make seed

# Seed ChromaDB with schema docs and Q&A retrieval examples
make seed-vectors
```

**Seeding takes a few minutes** on first run — ClickHouse downloads and ingests a ~5M-row GitHub Archive sample.

> **No internet access? Use the local seed instead.**
>
> If you are in a workshop environment without reliable internet, or if the GitHub Archive S3 source is slow, use the built-in offline fallback:
>
> ```bash
> make seed LOCAL=1
> ```
>
> This loads 18 hand-crafted rows across three repositories that are specifically designed to reproduce the ghost-contributor pattern. Acts 2 and 3 work identically with this dataset.
>
> Also set `LOCAL_SEED=true` in your `.env` file so the TUI and `python -m agentic_system.demo` automatically use the matching demo question and hint text:
>
> ```bash
> # .env
> LOCAL_SEED=true
> ```
>
> **Expected results with the local dataset (pre-migration)**
>
> Dataset overview — 18 rows total:
>
> | repo | total events | PRs opened | PRs merged | PRs rejected |
> |------|-------------|-----------|-----------|-------------|
> | `org/repo-alpha` | 7 | 3 | 2 | 2 |
> | `org/repo-beta` | 6 | 2 | 2 | 2 |
> | `org/repo-gamma` | 5 | 2 | 2 | 1 |
>
> All contributors:
>
> | actor | repo | PRs opened | PRs merged | ghost? |
> |-------|------|-----------|-----------|--------|
> | `alice` | `org/repo-alpha` | 1 | 1 | no |
> | `bob` | `org/repo-alpha` | 0 | 1 | no |
> | `ghost-user-1` | `org/repo-alpha` | 2 | 0 | **yes** |
> | `carol` | `org/repo-beta` | 0 | 2 | no |
> | `ghost-user-2` | `org/repo-beta` | 1 | 0 | **yes** |
> | `ghost-user-3` | `org/repo-beta` | 1 | 0 | **yes** |
> | `dave` | `org/repo-gamma` | 0 | 2 | no |
> | `ghost-user-4` | `org/repo-gamma` | 2 | 0 | **yes** |
>
> Ghost contributor query — **Act 1 expected output** (4 rows):
>
> | actor | repo | prs_opened | prs_merged |
> |-------|------|-----------|-----------|
> | `ghost-user-1` | `org/repo-alpha` | 2 | 0 |
> | `ghost-user-2` | `org/repo-beta` | 1 | 0 |
> | `ghost-user-3` | `org/repo-beta` | 1 | 0 |
> | `ghost-user-4` | `org/repo-gamma` | 2 | 0 |
>
> **Act 2 expected output** (after `make migrate`): **0 rows** — the agent generates `merged = 1` but the column is now zeroed out. No exception, no warning. This is the silent failure.
>
> **Act 3 expected output** (after `make schema-sync`): same 4 rows as Act 1, now using `merged_at IS NOT NULL` in the SQL.

Verify services are up:

| Service | URL |
|---------|-----|
| ClickHouse HTTP | http://localhost:8123 |
| ChromaDB | http://localhost:8000 |
| MLflow UI | http://localhost:5002 |

---

## 6. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Textual TUI (terminal)                     │
│   Chat panel (Q&A history)  │  Agent Trace panel (tool calls) │
│   ─────────────────────────────────────────────────────────  │
│   ConversationMemory — session-scoped turn history            │
└──────────────────────────┬───────────────────────────────────┘
                           │  Runner.run_streamed(orchestrator, history + question)
┌──────────────────────────▼───────────────────────────────────┐
│                 GithubDataOrchestrator                        │
│                 (OpenAI Agents SDK)                           │
│                                                               │
│   tools: [retrieve_schema_context, query_github_data]         │
└────────────────┬────────────────────────┬─────────────────── ┘
                 │ as_tool()              │ as_tool()
┌────────────────▼──────────┐  ┌──────────▼────────────────────┐
│          AgentRAG          │  │         AgentNL2SQL            │
│                            │  │                                │
│  tool: vector_search       │  │  tool: run_sql                 │
└────────────────┬──────────┘  └──────────┬────────────────────┘
                 │                         │
        ┌────────▼────────┐      ┌─────────▼──────────┐
        │    ChromaDB     │      │     ClickHouse      │
        │  (vector store) │      │  (analytics SQL)    │
        │  :8000          │      │  :8123              │
        └─────────────────┘      └────────────────────-┘

┌──────────────────────────────────────────────────────────────┐
│                       Observability                           │
│  MLflow autolog  →  http://localhost:5002  (traces + runs)   │
│  loguru file sink  →  logs/session_<timestamp>.log           │
└──────────────────────────────────────────────────────────────┘
```

### Pattern: AgentAsTools

The orchestrator never touches a database directly. It delegates all data work to two specialised sub-agents exposed as callable tools:

| Tool | Backed by | Responsibility |
|------|-----------|----------------|
| `retrieve_schema_context` | `AgentRAG` | Searches ChromaDB for relevant field descriptions and SQL examples |
| `query_github_data` | `AgentNL2SQL` | Generates ClickHouse SQL, executes it, returns rows |

**Per-question flow:**

1. Orchestrator calls `retrieve_schema_context(question)` → gets schema context from ChromaDB.
2. Orchestrator calls `query_github_data(question + context)` → gets SQL + result rows from ClickHouse.
3. Orchestrator synthesises a plain-language answer.

### Conversation Memory

`ConversationMemory` stores the full turn history using `result.to_input_list()` after each run. This lets the agent answer follow-up questions with full context of previous turns — no need to repeat repository names or filter conditions.

```
Turn 1:  "Show me ghost contributors on kubernetes/kubernetes"
         → agent queries and remembers the exchange

Turn 2:  "Who has the most rejected PRs from that repo?"
         → agent sees Turn 1 context, no disambiguation needed
```

Press `Ctrl+L` in the TUI to clear memory and start a fresh session.

---

## 7. The Use Case — Ghost Contributors

> *"Show me repositories where users opened pull requests but never got one merged — the ghost contributors."*

A **ghost contributor** is a developer who submitted one or more pull requests to a repository but never had a single PR merged. They put in the effort, received no acceptance, and likely moved on.

The GitHub Archive dataset contains millions of pull request events. The agentic system translates the natural language question into a ClickHouse SQL query, executes it, and returns the result — without the user writing a single line of SQL.

**Example questions you can ask:**

- `Show me ghost contributors on kubernetes/kubernetes`
- `Which repositories have the highest PR rejection rate in 2023?`
- `Who has the most unmerged PRs in the dataset?`
- `How many ghost contributors are there across all repos?`

The key field driving this query is `merged` — a `UInt8` column where `1` means the PR was merged. This becomes important in Act 2.

---

## 8. The Three-Act Demo

### Act 1 — It Works

Launch the TUI (set `PYTHONPATH` first ) and ask the ghost contributor question:

```bash
export PYTHONPATH=/your/project/folder/skills_talk_agent_camp_2026
uv run python agentic_system/main.py
```

The TUI opens with two panels — the **Chat panel** on the left and the **Agent Trace panel** on the right. Type your question and press `Enter`:

```
Show me ghost contributors on kubernetes/kubernetes
```

**What you will see:**

- The trace panel shows the orchestrator calling `retrieve_schema_context` then `query_github_data`.
- `AgentRAG` retrieves schema docs from ChromaDB confirming `merged UInt8` field semantics.
- `AgentNL2SQL` generates SQL using `WHERE merged = 1` / `WHERE merged = 0` and returns rows.
- The chat panel displays a plain-language answer with the contributor list.

**TUI controls:**

| Key | Action |
|-----|--------|
| `Enter` | Submit question |
| `Ctrl+L` | Clear chat and reset memory |
| `Ctrl+C` | Quit |

The system works correctly because the schema contract, ChromaDB retrieval context, NL2SQL prompt, and RAG prompt all agree: `merged` is a `UInt8` field.

---

### Act 2 — It Breaks

A schema migration renames the field from `merged UInt8` to `merged_at Nullable(DateTime)`. This is a realistic, well-intentioned change — better semantics, richer data.

```bash
make migrate
```

Now run the same question in the TUI again.

**What breaks silently:**

| Layer | What happens |
|-------|-------------|
| ClickHouse schema | `merged` column now stores zeros only; `merged_at IS NOT NULL` is the correct filter |
| YAML contract | Still declares `merged UInt8` — drift is now present |
| NL2SQL prompt | Still instructs the agent to use `merged = 1` — query returns 0 rows |
| RAG prompt + ChromaDB | Still return `merged UInt8` context — reinforces wrong SQL generation |

The agent returns **0 rows with no error**. No exception, no warning — a silent wrong answer. This is the most dangerous failure mode: the system appears healthy.

You can confirm the drift explicitly:

```bash
make validate-schema
```

---

### Act 3 — It Heals

`schema_sync` repairs all four layers in one command. This is the **Skill** in action.

```bash
make schema-sync
```

**What schema-sync does:**

```
── Step 1/4  ClickHouse introspect
  Reads live schema: merged_at Nullable(DateTime) detected

── Step 2/4  YAML contract patch
  Updates github_events.yaml — adds merged_at, refreshes merged description

── Step 3/4  ChromaDB chunk patch
  Finds stale chunks (metadata.stale == True)
  Replaces merged UInt8 references → merged_at Nullable(DateTime)
  Re-embeds updated chunks

── Step 4/4  Agent prompt patch
  Patches nl2sql/prompts/system.md — merged = 1 → merged_at IS NOT NULL
  Patches rag/prompts/system.md    — field semantic description updated
```

Run the same question again in the TUI. The agent now generates correct SQL using `merged_at IS NOT NULL` and returns the expected rows.

**Dry-run mode** (preview without touching anything):

```bash
make schema-sync-dry
```

**Rollback** (undo the sync):

```bash
uv run python dev_tools/schema_sync.py --table github_events --rollback
```

**Reset to pre-migration state** (full rollback including ClickHouse):

```bash
make rollback
```

---

## 9. Skills — The Core Concept

A **Skill** is a structured, reusable procedure that tells Claude exactly what to do in a given situation. The quality of the Skill determines the reliability of the outcome.

The `dev_tools/skill_examples/` directory contains four versions of the same repair procedure at increasing levels of guidance:

### The Skill Progression

```
skill_examples/
├── 00_naive/           # "Something broke — investigate and fix."
├── 01_structured/      # Names the four layers; points to validate_schema.py
├── 02_agent_assisted/  # Adds context table + ordered six-step procedure
└── 03_fully_guided/    # One-command fix, fallback steps, pre/post validation, rollback
```

| Level | What Claude gets | Outcome |
|-------|-----------------|---------|
| `00_naive` | A vague instruction | High exploration cost; easy to miss a layer |
| `01_structured` | The four layer names | Knows where to look; still guesses the fix |
| `02_agent_assisted` | Ordered repair steps | Coherent workflow; no exact replacement rules |
| `03_fully_guided` | Full procedure with commands, validation, rollback | Deterministic, repeatable repair |

**The key insight:** `schema_sync.py` is the code implementation of the `03_fully_guided` Skill. Once you have a fully guided Skill, automating it into a script is straightforward. The Skill comes first — it forces you to understand the procedure well enough to formalise it.

### The Principle

Schema migrations are **predictable events**. The next time a field is renamed, the fix is:

```bash
make migrate && uv run python dev_tools/schema_sync.py --table github_events
```

That predictability is the value of formalising the response as a Skill.

---

## 10. Running the Tests

The test suite runs fully offline — no live services or API keys required. All database interactions are mocked.

```bash
# Run all tests
uv run pytest

# Run by act
uv run pytest -m pre_migration       # Act 1: pre-migration baseline
uv run pytest -m post_migration      # Act 2: silent failure verification
uv run pytest -m schema_sync         # Act 3: repair contract
uv run pytest -m complete_flow       # Full stateful lifecycle
```

| Test file | What it covers |
|-----------|---------------|
| `tests/test_use_case.py` | Ghost contributor query behaviour pre- and post-migration |
| `tests/test_schema_sync.py` | Four-layer patch outcome + unit tests for each patch utility |
| `tests/test_agents.py` | Prompt field names pre- and post-sync |
| `tests/test_complete_flow_mocked.py` | Stateful lifecycle: pre → migrate → schema_sync → fixed |

CI runs the full suite on every push via GitHub Actions (`.github/workflows/`).

---

### Special test: `schema_upgrade_gate`

`tests/test_schema_upgrade_gate.py` is a strict post-migration readiness gate. It checks that every layer of the repository — the YAML schema contract, the NL2SQL prompt, the RAG prompt, and the agent tool description — has been fully updated to use `merged_at` instead of `merged`.

**This test is designed to fail in the pre-migration state.** Running it before Act 3 is a way to confirm that the system is genuinely broken across all four layers.

```bash
uv run pytest tests/test_schema_upgrade_gate.py -q
```

Expected output **before `make schema-sync`** (Act 2 state — 5 failures):

```
FAILED tests/test_schema_upgrade_gate.py::test_repo_code_is_upgraded_for_post_migration_schema
Post-migration code upgrade gate failed:
- Schema contract missing `merged_at` column.
- Schema contract still documents legacy predicate `merged = 1`.
- NL2SQL prompt still contains `merged = 1`.
- RAG prompt missing `merged_at` reference.
- Agent tool description still advertises `merged = 1`.
```

Expected output **after `make schema-sync`** (Act 3 — all pass):

```
1 passed
```

This gate is intentionally excluded from the standard CI suite (`pre_migration or post_migration or schema_sync or complete_flow`). It lives as a separate profile because it is only meaningful to run at the Act 2 → Act 3 transition — not as a regression check on the pre-migration baseline.

---

## 11. Observability

### MLflow

Every agent run is traced automatically via `mlflow.openai.autolog()`. Each question creates a root MLflow run with nested spans for the orchestrator, `AgentRAG`, and `AgentNL2SQL` tool calls.

Open the MLflow UI at **http://localhost:5002** and navigate to the `ghost-contributors-demo` experiment to see:

- Full LLM call traces with token counts
- SQL queries generated by `AgentNL2SQL`
- ChromaDB retrieval results from `AgentRAG`
- End-to-end latency per question

The current MLflow run URL is also displayed live in the TUI trace panel during each query.

### Logs

`loguru` writes a rotating session log to `logs/session_<timestamp>.log`. Standard output is intentionally suppressed so the Textual TUI owns the terminal cleanly. Inspect logs after a session:

```bash
cat logs/session_*.log | tail -100
```

---

## 12. Teardown

Stop the infrastructure stack:

```bash
make down
```

Full reset (removes all data volumes — next `make up` starts from scratch):

```bash
make reset
```

Nuclear clean (removes containers, images, volumes, and frees ports):

```bash
make clean-complete
```

---

## 13. Reference — All Commands

### Infrastructure

| Command | Description |
|---------|-------------|
| `make up` | Start ClickHouse, ChromaDB, and MLflow |
| `make down` | Stop all services |
| `make seed` | Seed ClickHouse with ~5M GitHub Archive PR events (requires internet) |
| `make seed LOCAL=1` | Seed ClickHouse with 18-row local dataset — ghost-contributor pattern, no internet needed |
| `make seed-vectors` | Seed ChromaDB collections |
| `make logs` | Tail service logs |
| `make reset` | Recreate infrastructure from scratch (clears volumes) |
| `make clean-complete` | Nuclear clean — stop, remove images, volumes, free ports |

### Demo Flow

| Command | Description |
|---------|-------------|
| `uv run python agentic_system/main.py` | Launch the TUI |
| `make migrate` | Act 2 — rename `merged → merged_at` (triggers silent failure) |
| `make validate-schema` | Diff live ClickHouse schema vs YAML contract |
| `make schema-sync` | Act 3 — patch all four layers |
| `make schema-sync-dry` | Preview schema-sync changes without applying them |
| `make rollback` | Restore pre-migration schema and ChromaDB state |

### schema_sync.py direct usage

```bash
uv run python dev_tools/schema_sync.py --table github_events
uv run python dev_tools/schema_sync.py --table github_events --dry-run
uv run python dev_tools/schema_sync.py --table github_events --rollback
```

### Tests

| Command | Description |
|---------|-------------|
| `uv run pytest` | Run all tests |
| `uv run pytest -m pre_migration` | Act 1 tests |
| `uv run pytest -m post_migration` | Act 2 tests |
| `uv run pytest -m schema_sync` | Act 3 tests |
| `uv run pytest -m complete_flow` | Full stateful lifecycle test |
| `make test-complete-flow` | Shortcut for the mocked stateful flow test |
| `make verify-complete-flow` | Live sequential verification with auto-rollback |
| `uv run pytest tests/test_schema_upgrade_gate.py -q` | Post-migration readiness gate — fails in Act 2, passes after Act 3 |

---

*AgentCamp 2026 — Skills Talk*
