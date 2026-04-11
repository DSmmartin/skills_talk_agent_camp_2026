---
id: AGT-01
name: AgentRAG — Definition, System Prompt, Few-Shot Examples, vector_search Tool
epic: Epic 2 - Agentic System (Act 1)
status: [x] Done
summary: Build the AgentRAG sub-agent with its system prompt, few-shot examples, and ChromaDB vector_search tool.
---

# AGT-01 - AgentRAG — Definition, System Prompt, Few-Shot Examples, vector_search Tool

- Epic: Epic 2 - Agentic System (Act 1)
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L627)

## Objective

Create the AgentRAG sub-agent so the orchestrator has a callable tool that retrieves schema context and SQL examples from ChromaDB.

## Description

AgentRAG is exposed to the root orchestrator via `as_tool()`. It owns its own system prompt and few-shot examples — two of the four layers broken during Act 2 and healed by `schema_sync` in Act 3. The agent's sole callable tool is `vector_search`, which performs semantic search against ChromaDB. The system prompt and examples files are stored as separate markdown files so `schema_sync` can patch them without touching Python source.

## Scope

- Create `agentic_system/agents_core/rag/agent.py` with the AgentRAG definition using the OpenAI Agents SDK.
- Create `agentic_system/agents_core/rag/prompts/system.md` with the RAG system prompt.
- Create `agentic_system/agents_core/rag/prompts/examples.md` with few-shot examples referencing the pre-migration schema (`merged UInt8`).
- Create `agentic_system/agents_core/rag/tools/vector_search.py` implementing semantic search against ChromaDB.
- Expose AgentRAG as a tool via `agent_rag.as_tool(tool_name="retrieve_schema_context", ...)`.

## Out Of Scope

- Root orchestrator wiring (AGT-03).
- NL2SQL agent (AGT-02).
- MLflow / OpenAI client setup (AGT-07).
- ChromaDB seeding (covered by Epic 1, INF-05).
- Schema migration or schema-sync patching.

## Deliverables

- `agentic_system/__init__.py`, `agentic_system/agents_core/__init__.py`, `agentic_system/agents_core/rag/__init__.py`, `agentic_system/agents_core/rag/tools/__init__.py` — package markers.
- `agentic_system/config.py` — `Settings` via `pydantic-settings`; single source for all connection config.
- `agentic_system/agents_core/rag/agent.py` — `agent_rag` definition and `rag_tool` export.
- `agentic_system/agents_core/rag/prompts/system.md` — system prompt, patchable by schema-sync.
- `agentic_system/agents_core/rag/prompts/examples.md` — few-shot examples using pre-migration field names.
- `agentic_system/agents_core/rag/tools/vector_search.py` — ChromaDB semantic search tool.

## Acceptance Criteria

- `AgentRAG` is defined using the OpenAI Agents SDK with `model="gpt-4o"`.
- `vector_search` tool connects to ChromaDB and returns relevant chunks for a given query string.
- `rag_tool = agent_rag.as_tool(tool_name="retrieve_schema_context", ...)` is importable from `agentic_system.agents_core.rag.agent`.
- System prompt and examples files exist as separate files under `prompts/` — not inlined in Python.
- Few-shot examples in `examples.md` use `merged UInt8` / `merged = 1` (pre-migration field names).

## Dependencies

- INF-04, INF-05: ChromaDB running and seeded with schema docs and Q&A examples (runtime only).
- AGT-04: `agentic_system/schema/github_events.yaml` available so vector_search context aligns with the schema.

## Assumptions

- OpenAI Agents SDK (`openai-agents`) is the framework for agent definitions.
- ChromaDB is accessible at the connection string defined in `agentic_system/config.py`.
- Few-shot examples intentionally use pre-migration field names — patched by schema-sync in Act 3.

## Verification

Procedure used to verify the task against the local Python environment:

1. Parse all delivered Python files with `ast.parse` to confirm syntax is valid.
2. Import `agent_rag` and `rag_tool` from `agentic_system.agents_core.rag.agent` and assert expected attributes.
3. Confirm prompt files load at import time with non-zero content.

Commands used:

```bash
# Syntax check
source .venv/bin/activate && python3 -c "
import ast
files = [
    'agentic_system/__init__.py',
    'agentic_system/config.py',
    'agentic_system/agents_core/__init__.py',
    'agentic_system/agents_core/rag/__init__.py',
    'agentic_system/agents_core/rag/agent.py',
    'agentic_system/agents_core/rag/tools/__init__.py',
    'agentic_system/agents_core/rag/tools/vector_search.py',
]
for f in files:
    with open(f) as fh:
        ast.parse(fh.read())
    print(f'  OK  {f}')
"

# Runtime import and attribute verification
source .venv/bin/activate && python3 -c "
from agentic_system.agents_core.rag.agent import agent_rag, rag_tool
from pathlib import Path

print('name:            ', agent_rag.name)
print('model:           ', agent_rag.model)
print('tools:           ', [t.name for t in agent_rag.tools])
print('instructions len:', len(agent_rag.instructions), 'chars')
print('rag_tool type:   ', type(rag_tool).__name__)
print('rag_tool name:   ', rag_tool.name)
print('rag_tool desc:   ', rag_tool.description)
base = Path('agentic_system/agents_core/rag/prompts')
for f in sorted(base.iterdir()):
    print(f'  {f.name}: {len(f.read_text())} chars')
"
```

Expected verification result (observed on 2026-04-07):

```
# Syntax check
  OK  agentic_system/__init__.py
  OK  agentic_system/config.py
  OK  agentic_system/agents_core/__init__.py
  OK  agentic_system/agents_core/rag/__init__.py
  OK  agentic_system/agents_core/rag/agent.py
  OK  agentic_system/agents_core/rag/tools/__init__.py
  OK  agentic_system/agents_core/rag/tools/vector_search.py

# Runtime
name:             AgentRAG
model:            gpt-4o
tools:            ['vector_search']
instructions len: 2304 chars
rag_tool type:    FunctionTool
rag_tool name:    retrieve_schema_context
rag_tool desc:    Retrieves schema field descriptions and SQL examples relevant to the question from the vector database. Call this first before generating any SQL.
  examples.md: 1703 chars
  system.md: 599 chars
```

Note: `vector_search` connects to ChromaDB at runtime — a live ChromaDB instance (INF-04/INF-05) is required for end-to-end execution. Import and attribute checks run fully offline.

## Notes

- The `prompts/` files are the primary patch targets for `schema_sync` in Act 3. Keep them as standalone files.
- The `tool_description` passed to `as_tool()` is also a patch target; keep it concise and field-name-aware.
- Completed 2026-04-07. `pydantic-settings` used for config; `chromadb.HttpClient` for vector search; `@function_tool` decorator from openai-agents SDK.
- `agentic_system/config.py` was later extended in AGT-03 with Azure OpenAI fields and `openai_provider` selector — no changes required in this task's files.
