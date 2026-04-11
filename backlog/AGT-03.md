---
id: AGT-03
name: Root Orchestrator — Generic Agent[DemoContext] with Azure/OpenAI Setup
epic: Epic 2 - Agentic System (Act 1)
status: [x] Done
summary: Build the generic GitHub Archive orchestrator, OpenAI/Azure client setup, credentials models, and demo runner helper.
---

# AGT-03 - Root Orchestrator — Generic Agent[DemoContext] with Azure/OpenAI Setup

- Epic: Epic 2 - Agentic System (Act 1)
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L629)

## Objective

Create a fully generic GitHub Archive query orchestrator typed with `Agent[DemoContext]`, a provider-agnostic OpenAI client setup module, Pydantic credential models, and a demo runner helper that keeps the ghost-contributor question separate from the orchestrator logic.

## Description

The orchestrator does not access any database directly — it delegates to `rag_tool` and `nl2sql_tool` via the AgentAsTools pattern. It answers any GitHub Archive question, not just ghost contributors. The demo question is defined in `agentic_system/demo.py` and run via `Runner.run(orchestrator, question)`.

The `setup_openai()` function in `agentic_system/setup.py` must be called once at process start. It selects between Azure OpenAI and default OpenAI based on `OPENAI_PROVIDER`, calls `mlflow.openai.autolog()` for automatic LLM tracing, and disables the built-in agents SDK tracing via `set_tracing_disabled(True)` so only MLflow tracing is active.

## Scope

- Create `agentic_system/models.py` with `AzureOpenAICredentials` and `OpenAICredentials`.
- Create `agentic_system/setup.py` with `setup_openai()` handling both providers.
- Rewrite `agentic_system/orchestrator.py` as a generic `Agent[DemoContext]` named `GithubDataOrchestrator`.
- Create `agentic_system/demo.py` with `DEMO_QUESTION`, `run_query()` (async), and `run_query_sync()`.
- Extend `agentic_system/config.py` with Azure OpenAI fields and `openai_provider` selector.
- Extend `.env.example` with all OpenAI provider variables.

## Out Of Scope

- TUI wiring (AGT-05, AGT-08).
- loguru setup (AGT-06).
- AgentRAG and AgentNL2SQL definitions (AGT-01, AGT-02).
- Migration or schema-sync logic.

## Deliverables

- `agentic_system/models.py` — `AzureOpenAICredentials` (Pydantic), `OpenAICredentials` (Pydantic).
- `agentic_system/setup.py` — `setup_openai()` with Azure/default branching, `mlflow.openai.autolog()`, `set_tracing_disabled(True)`.
- `agentic_system/orchestrator.py` — `GithubDataOrchestrator = Agent[DemoContext](...)` with both sub-agent tools.
- `agentic_system/demo.py` — `DEMO_QUESTION`, `run_query(question, context)`, `run_query_sync(question, context)`.
- `agentic_system/config.py` — extended with `openai_provider`, `azure_openai_*` fields.
- `.env.example` — extended with all OpenAI provider variables.

## Acceptance Criteria

- `orchestrator` is `Agent` with `name="GithubDataOrchestrator"` and `model="gpt-4o"`.
- `tools=[rag_tool, nl2sql_tool]` are both present.
- No direct database imports exist in `orchestrator.py`.
- `setup_openai()` calls `mlflow.openai.autolog()`, sets the default client for both Azure and default OpenAI, and calls `set_tracing_disabled(True)`.
- `AzureOpenAICredentials.from_env()` and `OpenAICredentials.from_env()` load from `settings`.
- `run_query(question)` returns `await Runner.run(orchestrator, question)`.

## Dependencies

- AGT-01: `rag_tool` importable from `agentic_system.agents_core.rag.agent`.
- AGT-02: `nl2sql_tool` importable from `agentic_system.agents_core.nl2sql.agent`.

## Assumptions

- The orchestrator follows the AgentAsTools pattern — it never calls databases directly.
- `setup_openai()` is called once before any agent runs, in `agentic_system/main.py` (AGT-08).
- The demo question is intentionally kept outside the orchestrator to preserve reusability.

## Verification

Procedure used to verify the task against the local Python environment:

1. Parse all delivered Python files with `ast.parse`.
2. Import all modules and assert expected attributes on each.
3. Verify `orchestrator.py` has no direct DB imports via AST scan.
4. Verify `setup.py` contains all required SDK calls via source inspection.

Commands used:

```bash
# Syntax check
source .venv/bin/activate && python3 -c "
import ast
files = [
    'agentic_system/config.py',
    'agentic_system/models.py',
    'agentic_system/setup.py',
    'agentic_system/orchestrator.py',
    'agentic_system/demo.py',
]
for f in files:
    with open(f) as fh:
        ast.parse(fh.read())
    print(f'  OK  {f}')
"

# Runtime import and attribute verification
source .venv/bin/activate && python3 -c "
from agentic_system.orchestrator import orchestrator
from agentic_system.models import AzureOpenAICredentials, OpenAICredentials, DemoContext
from agentic_system.config import settings
import ast, pathlib

print('orchestrator.name:  ', orchestrator.name)
print('orchestrator.model: ', orchestrator.model)
print('orchestrator.tools: ', [t.name for t in orchestrator.tools])
print('orchestrator.instr: ', len(orchestrator.instructions), 'chars')

tree = ast.parse(pathlib.Path('agentic_system/orchestrator.py').read_text())
imports = [
    node.names[0].name if isinstance(node, ast.Import) else node.module
    for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
]
db = [i for i in imports if i and any(x in i for x in ('clickhouse','chromadb','sqlite'))]
print('direct DB imports:  ', db or 'none')

ctx = DemoContext()
print('AzureOpenAI fields:', list(AzureOpenAICredentials.model_fields.keys()))
print('OpenAI fields:     ', list(OpenAICredentials.model_fields.keys()))
print('config.provider:   ', settings.openai_provider)

src = pathlib.Path('agentic_system/setup.py').read_text()
for label, token in [
    ('mlflow.openai.autolog()',  'mlflow.openai.autolog()'),
    ('set_default_openai_client','set_default_openai_client'),
    ('set_default_openai_api',   'set_default_openai_api'),
    ('set_tracing_disabled',     'set_tracing_disabled'),
    ('AsyncAzureOpenAI branch',  'AsyncAzureOpenAI'),
    ('AsyncOpenAI branch',       'AsyncOpenAI'),
]:
    print(f'  {\"OK\" if token in src else \"MISSING\"}  {label}')
"
```

Expected verification result (observed on 2026-04-07):

```
# Syntax check
  OK  agentic_system/config.py
  OK  agentic_system/models.py
  OK  agentic_system/setup.py
  OK  agentic_system/orchestrator.py
  OK  agentic_system/demo.py

# Runtime
orchestrator.name:   GithubDataOrchestrator
orchestrator.model:  gpt-4o
orchestrator.tools:  ['retrieve_schema_context', 'query_github_data']
orchestrator.instr:  1058 chars
direct DB imports:   none
AzureOpenAI fields: ['azure_endpoint', 'api_key', 'api_version', 'deployment']
OpenAI fields:      ['api_key']
config.provider:    openai
  OK  mlflow.openai.autolog()
  OK  set_default_openai_client
  OK  set_default_openai_api
  OK  set_tracing_disabled
  OK  AsyncAzureOpenAI branch
  OK  AsyncOpenAI branch
```

## Notes

- Orchestrator is named `GithubDataOrchestrator` — not scoped to ghost contributors.
- The ghost contributor demo question lives in `agentic_system/demo.py::DEMO_QUESTION`.
- `mlflow.openai.autolog()` in `setup.py` supersedes the custom decorator approach originally planned in AGT-07. AGT-07 has been revised accordingly.
- `DemoContext` was introduced and then removed — `Runner.run` is called without a context argument. No tool needs run-scoped dependency injection at this stage.
- Completed 2026-04-07.
