---
id: AGT-02
name: AgentNL2SQL — Definition, System Prompt, Few-Shot SQL Examples, run_sql Tool
epic: Epic 2 - Agentic System (Act 1)
status: [x] Done
summary: Build the AgentNL2SQL sub-agent with its system prompt, few-shot SQL examples, and ClickHouse run_sql tool.
---

# AGT-02 - AgentNL2SQL — Definition, System Prompt, Few-Shot SQL Examples, run_sql Tool

- Epic: Epic 2 - Agentic System (Act 1)
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L628)

## Objective

Create the AgentNL2SQL sub-agent so the orchestrator has a callable tool that translates natural language questions into ClickHouse SQL and returns query results.

## Description

AgentNL2SQL is exposed to the root orchestrator via `as_tool()`. It receives a natural language question plus schema context retrieved by AgentRAG, generates SQL, executes it against ClickHouse, and returns both results and the SQL used. Like AgentRAG, it owns its own system prompt and few-shot SQL examples as separate files — these are two of the four layers broken by the Act 2 schema migration and healed by `schema_sync` in Act 3.

The `run_sql` tool is a thin wrapper around `clickhouse_connect`. Results are returned as JSON (`sql`, `row_count`, `rows`) so the TUI trace panel can parse and display the SQL without a second LLM call.

The system prompt embeds the full `github_events` table schema so the agent can answer basic questions without requiring RAG. When schema context is provided it takes priority — which makes it the correct patch target for `schema_sync` in Act 3.

## Scope

- Create `agentic_system/agents_core/nl2sql/agent.py` with the AgentNL2SQL definition using the OpenAI Agents SDK.
- Create `agentic_system/agents_core/nl2sql/prompts/system.md` with the NL2SQL system prompt, including the full `github_events` column table.
- Create `agentic_system/agents_core/nl2sql/prompts/examples.md` with few-shot SQL examples using pre-migration schema (`merged = 1`, `merged = 0`).
- Create `agentic_system/agents_core/nl2sql/tools/run_sql.py` implementing ClickHouse query execution.
- Expose AgentNL2SQL as a tool via `agent_nl2sql.as_tool(tool_name="query_github_data", ...)`.

## Out Of Scope

- Root orchestrator wiring (AGT-03).
- RAG agent (AGT-01).
- MLflow / OpenAI client setup (AGT-07).
- Schema migration or schema-sync patching.
- ClickHouse provisioning and seeding (Epic 1).

## Deliverables

- `agentic_system/agents_core/nl2sql/__init__.py`, `agentic_system/agents_core/nl2sql/tools/__init__.py` — package markers.
- `agentic_system/agents_core/nl2sql/agent.py` — `agent_nl2sql` definition and `nl2sql_tool` export.
- `agentic_system/agents_core/nl2sql/prompts/system.md` — system prompt with embedded `github_events` schema table; patchable by schema-sync.
- `agentic_system/agents_core/nl2sql/prompts/examples.md` — three few-shot SQL examples using pre-migration field names (`merged = 1`).
- `agentic_system/agents_core/nl2sql/tools/run_sql.py` — ClickHouse query execution tool returning JSON with `sql`, `row_count`, `rows`.

## Acceptance Criteria

- `AgentNL2SQL` is defined using the OpenAI Agents SDK with `model="gpt-4o"`.
- `run_sql` executes a SQL string against ClickHouse and returns a JSON string with `sql`, `row_count`, and `rows`.
- `nl2sql_tool = agent_nl2sql.as_tool(tool_name="query_github_data", ...)` is importable from `agentic_system.agents_core.nl2sql.agent`.
- System prompt and examples exist as separate files under `prompts/` — not inlined in Python.
- `system.md` includes the `github_events` column table with pre-migration field names.
- `examples.md` uses `merged = 1` and `merged = 0` (pre-migration predicates).
- The tool description maps "unmerged" to `merged = 0` (pre-migration — patched in Act 3).

## Dependencies

- INF-01, INF-02, INF-03: ClickHouse running and seeded with PR events (runtime only).
- `agentic_system/config.py` for ClickHouse connection string.

## Assumptions

- OpenAI Agents SDK is the framework for agent definitions.
- ClickHouse is accessible via the connection string defined in `agentic_system/config.py`.
- Few-shot examples intentionally use pre-migration predicates — patched by schema-sync in Act 3.

## Verification

Procedure used to verify the task against the local Python environment:

1. Parse all delivered Python files with `ast.parse` to confirm syntax is valid.
2. Import `agent_nl2sql` and `nl2sql_tool` from `agentic_system.agents_core.nl2sql.agent` and assert expected attributes.
3. Confirm prompt files load at import time with non-zero content and correct sizes.

Commands used:

```bash
# Syntax check
source .venv/bin/activate && python3 -c "
import ast
files = [
    'agentic_system/agents_core/nl2sql/__init__.py',
    'agentic_system/agents_core/nl2sql/agent.py',
    'agentic_system/agents_core/nl2sql/tools/__init__.py',
    'agentic_system/agents_core/nl2sql/tools/run_sql.py',
]
for f in files:
    with open(f) as fh:
        ast.parse(fh.read())
    print(f'  OK  {f}')
"

# Runtime import and attribute verification
source .venv/bin/activate && python3 -c "
from agentic_system.agents_core.nl2sql.agent import agent_nl2sql, nl2sql_tool
from pathlib import Path

print('name:            ', agent_nl2sql.name)
print('model:           ', agent_nl2sql.model)
print('tools:           ', [t.name for t in agent_nl2sql.tools])
print('instructions len:', len(agent_nl2sql.instructions), 'chars')
print('nl2sql_tool type:', type(nl2sql_tool).__name__)
print('nl2sql_tool name:', nl2sql_tool.name)
print('nl2sql_tool desc:', nl2sql_tool.description)
base = Path('agentic_system/agents_core/nl2sql/prompts')
for f in sorted(base.iterdir()):
    print(f'  {f.name}: {len(f.read_text())} chars')
"
```

Expected verification result (observed on 2026-04-07):

```
# Syntax check
  OK  agentic_system/agents_core/nl2sql/__init__.py
  OK  agentic_system/agents_core/nl2sql/agent.py
  OK  agentic_system/agents_core/nl2sql/tools/__init__.py
  OK  agentic_system/agents_core/nl2sql/tools/run_sql.py

# Runtime
name:             AgentNL2SQL
model:            gpt-4o
tools:            ['run_sql']
instructions len: 4372 chars
nl2sql_tool type: FunctionTool
nl2sql_tool name: query_github_data
nl2sql_tool desc: Translates a natural language question about GitHub contributors into ClickHouse SQL, executes it, and returns the results. Pass the schema context from retrieve_schema_context along with the question. Unmerged PRs use merged = 0; merged PRs use merged = 1.
  examples.md: 2135 chars
  system.md: 2235 chars
```

Note: `run_sql` connects to ClickHouse at runtime — a live ClickHouse instance (INF-01/INF-02/INF-03) is required for end-to-end execution. Import and attribute checks run fully offline.

## Notes

- The `tool_description` string and `prompts/examples.md` are explicit patch targets for `schema_sync`. Keep field names literal in both.
- `run_sql` returns a JSON string with `sql`, `row_count`, and `rows` keys — structured for TUI trace parsing.
- `system.md` has a self-healing rule: if schema context says `merged_at DateTime NULL`, the agent switches predicates automatically. This reduces the blast radius of Act 2 while still being patchable for Act 3.
- Completed 2026-04-07. `clickhouse_connect.get_client` used for query execution; `@function_tool` decorator from openai-agents SDK; results serialised via `json.dumps(default=str)` for ClickHouse date types.
- Revised 2026-04-07: `prompts/system.md` updated to embed the full `github_events` table schema.
