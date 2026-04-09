# Architecture — Ghost Contributors Agentic NL2SQL System

## Pattern: AgentAsTools

The system uses the **AgentAsTools** pattern from the OpenAI Agents SDK. Two specialised agents are wrapped as callable tools and exposed to a root orchestrator. The orchestrator never touches a database directly.

```
User (TUI)
   │
   │  natural-language question + conversation history
   ▼
┌──────────────────────────────────────────────────────────┐
│             GithubDataOrchestrator                        │
│             orchestrator.py                               │
│                                                           │
│  tools:                                                   │
│    retrieve_schema_context  ──►  AgentRAG                 │
│    query_github_data        ──►  AgentNL2SQL              │
└──────────────┬────────────────────────┬──────────────────┘
               │ as_tool()              │ as_tool()
┌──────────────▼──────────┐  ┌──────────▼──────────────────┐
│        AgentRAG          │  │       AgentNL2SQL            │
│  agents_core/rag/        │  │  agents_core/nl2sql/         │
│                          │  │                              │
│  system prompt: field    │  │  system prompt: schema       │
│  semantics + retrieval   │  │  table + SQL rules           │
│  rules                   │  │                              │
│  tool: vector_search     │  │  tool: run_sql               │
└──────────────┬──────────┘  └──────────┬────────────────── ┘
               │                        │
       ┌───────▼──────┐        ┌─────── ▼──────┐
       │   ChromaDB   │        │   ClickHouse  │
       │  :8000       │        │  :8123        │
       │              │        │               │
       │  schema_docs │        │  github_events│
       │  qa_examples │        │  (~5M rows)   │
       └──────────────┘        └───────────────┘
```

---

## Request Flow Per Question

Each user question follows a fixed three-step delegation sequence:

1. **Retrieve schema context** — Orchestrator calls `retrieve_schema_context` (AgentRAG), passing the question. AgentRAG issues a `vector_search` against ChromaDB and returns relevant field descriptions and SQL examples.

2. **Generate and execute SQL** — Orchestrator calls `query_github_data` (AgentNL2SQL), passing the question and the retrieved schema context. AgentNL2SQL generates ClickHouse SQL, executes it via `run_sql`, and returns the rows.

3. **Synthesise answer** — Orchestrator formats a plain-language answer from the SQL results and streams it to the TUI.

---

## Conversation Memory

`memory.py` provides session-scoped history. After each run, `result.to_input_list()` captures the full turn (user message + assistant message + tool calls + tool outputs) as a flat list. That list is prepended to the next question so the orchestrator has full prior context.

```
Turn 1:  question → run → result.to_input_list() → stored in ConversationMemory
Turn 2:  [Turn 1 history] + new question → run
```

Memory is cleared on `Ctrl+L` in the TUI.

---

## Four-Layer Schema Coupling

The system has **four components** that each encode field names from the ClickHouse schema. A field rename breaks all four simultaneously:

| Layer | File | What it encodes |
|-------|------|----------------|
| YAML contract | `agentic_system/schema/github_events.yaml` | Authoritative column definitions |
| ChromaDB chunks | `schema_docs`, `qa_examples` collections | RAG retrieval content |
| NL2SQL prompt | `agents_core/nl2sql/prompts/system.md` | Schema table + SQL generation rules |
| RAG prompt | `agents_core/rag/prompts/system.md` | Field semantics for retrieval |

This coupling is intentional for the demo — it lets Act 2 show a realistic silent failure where the agent returns 0 rows with no exception. `schema_sync.py` patches all four layers in one pass.

---

## Observability Stack

```
┌──────────────────────────────────────────────────────────┐
│                   Observability                           │
│                                                           │
│  MLflow (port 5002)                                       │
│    mlflow.openai.autolog() — every LLM call auto-traced   │
│    Root run per query → nested spans per sub-agent        │
│    Experiment: ghost-contributors-demo                    │
│                                                           │
│  loguru                                                   │
│    File sink: logs/session_<timestamp>.log                │
│    stdout disabled — TUI owns the terminal                │
│    Rotating per process launch                            │
└──────────────────────────────────────────────────────────┘
```

The built-in OpenAI Agents SDK tracing is disabled (`set_tracing_disabled(True)`) — MLflow is the single active tracing layer.

---

## Infrastructure

| Service | Port | Purpose |
|---------|------|---------|
| ClickHouse | 8123 (HTTP), 9000 (native) | SQL database — ~5M GitHub Archive PR events |
| ChromaDB | 8000 | Vector database — schema docs and Q&A examples |
| MLflow | 5002 | LLM trace and experiment tracking |

All three services run as Docker containers with persistent volumes. Managed via `docker-compose.yml`.

---

## File Map (Top Level)

```
.
├── agentic_system/          # Multi-agent system (Act 1 + core)
│   ├── main.py              # Entry point
│   ├── orchestrator.py      # Root orchestrator definition
│   ├── memory.py            # Session conversation memory
│   ├── agents_core/
│   │   ├── rag/             # AgentRAG + vector_search tool
│   │   └── nl2sql/          # AgentNL2SQL + run_sql tool
│   ├── schema/              # YAML schema contract (schema-sync target)
│   └── tui/                 # Textual terminal UI
│
├── scripts/                 # Infrastructure scripts
│   ├── migrate_schema.py    # Act 2: rename merged → merged_at
│   ├── rollback_schema.py   # Restore pre-migration state
│   └── validate_schema.py   # Diff live DB vs YAML contract
│
├── dev_tools/               # Act 3: schema-sync tooling
│   ├── schema_sync.py       # Main CLI — patches all four layers
│   ├── scripts/             # Individual patch utilities
│   └── skill_examples/      # Skill quality progression (00–03)
│
├── db/                      # Database init scripts and vector seeds
├── tests/                   # pytest suite (mocked, no live services)
├── docker-compose.yml        # Service orchestration
└── Makefile                  # Developer workflow targets
```

---

## Technology Choices

| Component | Technology | Reason |
|-----------|------------|--------|
| Agentic framework | OpenAI Agents SDK | Native `as_tool()` support for AgentAsTools pattern |
| SQL database | ClickHouse | Columnar, fast aggregations over millions of events |
| Vector database | ChromaDB | Simple HTTP API, persistent Docker volume |
| Embeddings | `text-embedding-3-small` | Low cost, sufficient for schema doc retrieval |
| LLM | gpt-4o (configurable) | Strong SQL generation; Azure OpenAI supported |
| TUI | Textual | Multi-panel layout with streaming output |
| Tracing | MLflow `openai.autolog()` | Zero-instrumentation automatic tracing |
| Logging | loguru | File-only sink; stdout stays clean for TUI |
| Python tooling | uv | Fast, reproducible environment management |
