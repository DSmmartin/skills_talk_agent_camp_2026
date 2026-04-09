# Agentic System

NL2SQL multi-agent system for querying the GitHub Archive dataset. Built on the **AgentAsTools** pattern using the OpenAI Agents SDK.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Textual TUI  (tui/app.py)               │
│  Chat pane (Q&A history)  │  Trace pane (tool calls)     │
│  ────────────────────────────────────────────────────    │
│  ConversationMemory (memory.py) — session history        │
└────────────────────────┬─────────────────────────────────┘
                         │  Runner.run_streamed(orchestrator, history + question)
┌────────────────────────▼─────────────────────────────────┐
│               GithubDataOrchestrator                      │
│               orchestrator.py                             │
│                                                           │
│   tools: [retrieve_schema_context, query_github_data]     │
└──────────────┬────────────────────────┬──────────────────┘
               │ as_tool()              │ as_tool()
┌──────────────▼──────────┐  ┌──────────▼──────────────────┐
│        AgentRAG          │  │       AgentNL2SQL            │
│  agents_core/rag/        │  │  agents_core/nl2sql/         │
│                          │  │                              │
│  tool: vector_search     │  │  tool: run_sql               │
└──────────────┬──────────┘  └──────────┬────────────────── ┘
               │                        │
       ┌───────▼──────┐        ┌─────── ▼──────┐
       │   ChromaDB   │        │   ClickHouse  │
       │   :8000      │        │   :8123       │
       └──────────────┘        └───────────────┘

┌──────────────────────────────────────────────────────────┐
│                   Observability                           │
│  MLflow autolog → http://localhost:5002                   │
│  loguru file sink → logs/session_<time>.log              │
└──────────────────────────────────────────────────────────┘
```

---

## Pattern: AgentAsTools

The orchestrator never calls any database directly. It delegates to two sub-agents, each exposed as a callable tool via `agent.as_tool(...)`:

| Tool name | Backed by | Does |
|-----------|-----------|------|
| `retrieve_schema_context` | `AgentRAG` | Searches ChromaDB for relevant field descriptions and SQL examples |
| `query_github_data` | `AgentNL2SQL` | Generates ClickHouse SQL from the question + schema context, executes it, returns rows |

Orchestrator workflow per question:

1. Call `retrieve_schema_context` with the question → get schema context from ChromaDB.
2. Call `query_github_data` with the question **and** the retrieved context → get SQL + rows from ClickHouse.
3. Synthesise a plain-language answer from the results.

---

## Conversation Memory

`memory.py` provides `ConversationMemory` — session-scoped history that lets the agent answer follow-up questions with full context of previous turns.

```
Turn 1:  "Show me ghost contributors on kubernetes/kubernetes"
         → agent queries, gets rows, remembers the exchange

Turn 2:  "Who has the most rejected PRs from that repo?"
         → agent sees Turn 1 context, no need to re-specify the repo
```

**How it works:**

After each run, `result.to_input_list()` returns the full turn history (user messages + assistant turns + tool calls + tool outputs) as a flat list. That list is passed as the `input` to the next `Runner.run_streamed` call, prepended with the new user message.

```python
# memory.py core
def build_input(self, question):
    if not self._history:
        return question                              # first turn: plain string
    return self._history + [{"role": "user", "content": question}]

def update(self, result):
    self._history = result.to_input_list()          # capture after every run
```

Memory is cleared when the user presses `Ctrl+L` in the TUI.

---

## TUI

`tui/app.py` is a [Textual](https://textual.textualize.io/) terminal application.

```
┌────────────────────────┬──────────────────────────┐
│  Chat                  │  Agent Trace             │
│                        │                          │
│  You                   │  ─── Run 1 ───           │
│    Show me ghost…      │  → retrieve_schema…      │
│                        │     query: ghost contr…  │
│  Agent thinking…       │  → query_github_data     │
│                        │     sql: SELECT repo…    │
│  Agent                 │     rows: 12             │
│    In kubernetes/…     │                          │
│    …                   │  ─── Run 2  [mem: 1 turn]│
│  You                   │  → retrieve_schema…      │
│    Who's the worst…    │  → query_github_data     │
│                        │     sql: SELECT actor…   │
│  Agent                 │     rows: 8              │
│    The top offender…   │                          │
└────────────────────────┴──────────────────────────┘
│ >  Type your question here…                       │
└────────────────────────────────────────────────────┘
```

| Key | Action |
|-----|--------|
| `Enter` | Submit question |
| `Ctrl+L` | Clear chat + reset memory |
| `Ctrl+C` | Quit |

---

## File Map

```
agentic_system/
├── README.md                                  this file
├── main.py                                    entry point — logger → setup_openai → TUI
├── config.py                                  Settings via pydantic-settings (.env)
├── models.py                                  AzureOpenAICredentials, OpenAICredentials
├── setup.py                                   setup_openai() — call once at process start
├── orchestrator.py                            GithubDataOrchestrator agent definition
├── memory.py                                  ConversationMemory — session turn history
├── demo.py                                    DEMO_QUESTION + run_query() helper (CLI)
│
├── agents_core/
│   ├── rag/
│   │   ├── agent.py                           AgentRAG definition + rag_tool export
│   │   ├── prompts/
│   │   │   ├── system.md                      RAG system prompt          ← schema-sync target
│   │   │   └── examples.md                    Few-shot retrieval examples ← schema-sync target
│   │   └── tools/
│   │       └── vector_search.py               @function_tool — ChromaDB semantic search
│   │
│   └── nl2sql/
│       ├── agent.py                           AgentNL2SQL definition + nl2sql_tool export
│       ├── prompts/
│       │   ├── system.md                      NL2SQL system prompt + schema  ← schema-sync target
│       │   └── examples.md                    Few-shot SQL examples           ← schema-sync target
│       └── tools/
│           └── run_sql.py                     @function_tool — ClickHouse query execution
│
├── schema/
│   └── github_events.yaml                     Machine-readable pre-migration schema contract
│
├── observability/
│   └── logger.py                              loguru file-only sink, stdout removed
│
└── tui/
    └── app.py                                 Textual app — chat + trace panels
```

---

## Setup

```bash
# 1. Start infrastructure (ClickHouse + ChromaDB + MLflow)
make up

# 2. Seed ClickHouse with ~5M GitHub Archive PR events
make seed

# 3. Seed ChromaDB with schema docs and Q&A examples
make seed-vectors

# 4. Launch the TUI
python agentic_system/main.py
```

---

## Running a query programmatically

```python
import asyncio
from agentic_system.setup import setup_openai
from agentic_system.demo import run_query, DEMO_QUESTION

setup_openai()  # must be called before any agent module is imported

result = asyncio.run(run_query(DEMO_QUESTION))
print(result.final_output)
```

Any question works — the orchestrator is not scoped to ghost contributors:

```python
result = asyncio.run(run_query(
    "Which repositories have the highest PR rejection rate in 2023?"
))
```

---

## Configuration

All settings are loaded from `.env` via `pydantic-settings`. Copy `.env.example` at the repo root and fill in your values.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_PROVIDER` | `openai` | `openai` for default OpenAI, `azure` for Azure OpenAI |
| `OPENAI_MODEL` | `gpt-4o` | Model name (or Azure deployment name) |
| `OPENAI_API_KEY` | — | Required when `OPENAI_PROVIDER=openai` |
| `AZURE_OPENAI_ENDPOINT` | — | Required when `OPENAI_PROVIDER=azure` |
| `AZURE_OPENAI_API_KEY` | — | Required when `OPENAI_PROVIDER=azure` |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | Azure API version |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` | Azure deployment name |
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `CLICKHOUSE_HOST` | `localhost` | ClickHouse host |
| `CLICKHOUSE_PORT` | `8123` | ClickHouse HTTP port |
| `CLICKHOUSE_USER` | `default` | ClickHouse user |
| `CLICKHOUSE_PASSWORD` | _(empty)_ | ClickHouse password |
| `CLICKHOUSE_DATABASE` | `default` | ClickHouse database |
| `MLFLOW_TRACKING_URI` | `http://localhost:5002` | MLflow tracking server |
| `MLFLOW_EXPERIMENT_NAME` | `ghost-contributors-demo` | MLflow experiment |

---

## Observability

- **MLflow** — `mlflow.openai.autolog()` captures every LLM call automatically as a nested trace (orchestrator → AgentRAG → AgentNL2SQL). View at `http://localhost:5002` under the `ghost-contributors-demo` experiment.
- **loguru** — file-only sink at `logs/session_<time>.log`. No stdout output so the Textual TUI owns the terminal cleanly. One file per process launch.
- Built-in agents SDK tracing is disabled via `set_tracing_disabled(True)` — MLflow is the single active tracing layer.

---

## Schema-sync patch targets

Four files are written with **pre-migration field names** (`merged UInt8`). They are the patch targets for `dev_tools/schema_sync.py` in Act 3 of the demo:

| File | What gets patched |
|------|-------------------|
| `agents_core/rag/prompts/system.md` | Field name references in retrieval instructions |
| `agents_core/rag/prompts/examples.md` | Few-shot examples using `merged = 1` |
| `agents_core/nl2sql/prompts/system.md` | Schema table + SQL rules |
| `agents_core/nl2sql/prompts/examples.md` | Few-shot SQL using `merged = 1` / `merged = 0` |

The machine-readable contract is `schema/github_events.yaml`. After `schema_sync` runs, these files and the YAML will reference `merged_at IS NOT NULL` / `merged_at IS NULL`.

---

## Tests

```bash
# Run Act 1 acceptance tests (no live services needed — mocks ClickHouse + ChromaDB)
pytest -m pre_migration
```

| Test | Verifies |
|------|----------|
| `test_ghost_contributor_query_pre_migration` | SQL uses `merged = 1`, returns non-empty rows |
| `test_rag_returns_correct_field_pre_migration` | RAG context contains `merged` + `UInt8`, not `merged_at` |
