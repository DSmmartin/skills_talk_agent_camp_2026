# Product Backlog
## "Ghost Contributors — Agentic NL2SQL with Self-Healing Schema"

> **Version:** 0.4
> **Date:** 2026-04-09
> **Status:** Epics 1–8 done (Improvements) — Epic 9 (Nice to Have) pending

---

## 1. Executive Summary

An **agentic NL2SQL system** built over the GitHub Archive dataset. Answers natural language questions about contributor behaviour using the **AgentAsTools** pattern — AgentRAG and AgentNL2SQL exposed as callable tools to a root orchestrator.

| Act | What happens | Point |
|-----|-------------|-------|
| **Act 1 — It works** | Agent answers "Who's churning contributors?" via AgentRAG + AgentNL2SQL | Multi-agent NL2SQL |
| **Act 2 — It breaks** | DB migration renames `merged` → `merged_at`; system returns wrong answers silently | Cascading failure |
| **Act 3 — It heals** | `schema-sync` detects drift and patches prompts, RAG, schema docs, and tool descriptions in one pass | Developer procedure |

**Key message:** Act 3 shows how easy it is to create repeatable developer procedures for fully expected situations. Schema migrations are predictable; `schema-sync` formalises the response.

---

## 2. The Story

### The Question (Act 1)
> *"Show me repositories where users opened PRs but never got one merged — the ghost contributors"*

### The Schema Break (Act 2)

| Before | After | Impact |
|--------|-------|--------|
| `merged UInt8` (0/1) | `merged_at DateTime NULL` | All `merged = 1` predicates return 0 rows silently |

Four layers break simultaneously: AgentNL2SQL prompt, AgentRAG prompt, YAML schema contract, ChromaDB RAG chunks.

### What schema-sync fixes (Act 3)
`schema-sync` introspects the live schema, diffs against `schema/github_events.yaml`, then patches all four layers: YAML, NL2SQL prompts, RAG prompts, and ChromaDB chunks. Prints a `SchemaSyncReport` listing every change made.

---

## 3. Demo Phases

### Phase 0 — Setup (not shown to audience)
```bash
make up
make seed          # ~5M rows from GitHub Archive (requires internet)
# make seed LOCAL=1  # offline fallback: 18 controlled rows — set LOCAL_SEED=true in .env
make seed-vectors
python agentic_system/main.py
```

### Phase 1 — Act 1: It Works (5 min)
- Type the ghost contributor question in the TUI
- Trace pane shows orchestrator → AgentRAG → AgentNL2SQL live
- MLflow UI shows nested spans with token counts and latency
- Ask 1–2 follow-up questions to demonstrate conversation memory

### Phase 2 — Act 2: The Schema Migration (3 min)
- Second terminal: `make migrate`
- Same question → agent returns 0 rows, no error
- MLflow trace reveals SQL still using `merged = 1`
- Audience sees: 4 layers broken by one field rename

### Phase 3 — Act 3: The Developer Tool (7 min)
- `python dev_tools/schema_sync.py --table github_events`
- Narrate each step: introspect → diff → patch YAML → re-embed RAG → patch prompts → print report
- Same question → correct rows again
- Show `dev_tools/skill_examples/` progression: from naive manual patch to fully guided procedure

---

## 4. Product Backlog

### Epic 1 — Infrastructure and Data ✅ Done

All infrastructure tasks complete. Services: ClickHouse (8123), ChromaDB (8000), MLflow (5000).
Cold-start verified on macOS Apple Silicon. See `db/README.md` for details.

| ID | Story | Status |
|----|-------|--------|
| INF-00 | Scaffold infrastructure baseline and task traceability | Done |
| INF-01 | ClickHouse Dockerfile + persistent volume | Done |
| INF-02 | ClickHouse init SQL: github_events (pre-migration schema) | Done |
| INF-03 | Seed script: ~5M PR events from GitHub Archive | Done |
| INF-04 | ChromaDB Dockerfile + persistent volume | Done |
| INF-05 | ChromaDB seed: schema docs + Q&A examples | Done |
| INF-06 | MLflow Dockerfile + tracking server (SQLite backend) | Done |
| INF-07 | docker-compose.yml wiring all three services | Done |
| INF-08 | .env.example and Makefile with all targets | Done |
| INF-09 | Verify cold-start on macOS (Apple Silicon) | Done |
| INF-10 | Verify cold-start on Linux | Done |

---

### Epic 2 — Agentic System (Act 1) ✅ Done

Full system implemented. See `agentic_system/README.md` for architecture, memory model, and TUI details.

| ID | Story | Status |
|----|-------|--------|
| AGT-01 | AgentRAG: definition, system prompt, few-shot examples, vector_search tool | Done |
| AGT-02 | AgentNL2SQL: definition, system prompt, few-shot SQL examples, run_sql tool | Done |
| AGT-03 | Root orchestrator: wraps AgentRAG + AgentNL2SQL via as_tool() | Done |
| AGT-04 | agentic_system/schema/github_events.yaml — machine-readable schema contract | Done |
| AGT-05 | Textual TUI: chat pane, agent trace pane, full-width input bar | Done |
| AGT-06 | loguru: file sink only, stdout disabled (TUI owns terminal) | Done |
| AGT-07 | MLflow autolog: mlflow.openai.autolog() capturing all LLM calls | Done |
| AGT-08 | agentic_system/main.py — entry point wiring logger, setup_openai, TUI | Done |
| AGT-09 | End-to-end: ghost contributor question returns correct rows | Done |
| AGT-10 | Conversation memory: session-scoped history via to_input_list() | Done |

---

### Epic 3 — Migration Scripts (Act 2) ✅ Done

All migration scripts implemented and verified. See individual backlog files for verification commands.

| ID | Story | Priority | Estimate | Status |
|----|-------|----------|----------|--------|
| MIG-01 | scripts/migrate_schema.py: adds merged_at, zeros out merged (silent failure) | P0 | S | Done |
| MIG-02 | Migration marks ChromaDB chunks stale — content intentionally left wrong | P0 | S | Done |
| MIG-03 | scripts/rollback_schema.py: restore merged values, drop merged_at, clear stale | P0 | S | Done |
| MIG-04 | scripts/validate_schema.py: diff live DB vs YAML contract, exit 1 on drift | P1 | S | Done |
| MIG-05 | Verified: `merged = 1` returns 0 rows silently — no exception thrown | P0 | S | Done |
| MIG-06 | Makefile targets: `make migrate`, `make rollback`, `make validate-schema` | P0 | S | Done |

---

### Epic 4 — Developer Tools (Act 3) ✅ Done

**The story of this epic is the `skill_examples/` progression.**

After `make migrate` breaks the agent, the PM says: *"The schema changed — fix the system."*
The demo question is: **"Who can write the best Skill?"**

Each `skill_examples/` subfolder contains a `SKILL.md` — a procedure written for Claude Code.
The progression shows four skill quality levels, from open/naive to fully guided:

| Level | Skill | What Claude gets |
|-------|-------|-----------------|
| 00 | `00_naive/SKILL.md` | "Something broke. Fix it." — no files, no steps |
| 01 | `01_structured/SKILL.md` | The four files to inspect and a validation command |
| 02 | `02_agent_assisted/SKILL.md` | Four-layer context table + six-step repair sequence |
| 03 | `03_fully_guided/SKILL.md` | One-command fix, step-by-step fallback, exact replacements, rollback |

The **balance point**: `00_naive` is maximally general but expensive and unreliable.
`03_fully_guided` is efficient and repeatable but specific to this migration pattern.
The `dev_tools/scripts/` and `schema_sync.py` are the tooling the `03_fully_guided` skill calls.

See `dev_tools/README.md` for full documentation.

| ID | Story | Priority | Estimate | Status |
|----|-------|----------|----------|--------|
| DEV-01 | skill_examples/00_naive/SKILL.md — naive skill: "something broke, fix it" | P0 | S | Done |
| DEV-02 | skill_examples/01_structured/SKILL.md — lists the four files/layers to inspect | P0 | S | Done |
| DEV-03 | skill_examples/02_agent_assisted/SKILL.md — four-layer table + six-step procedure | P1 | M | Done |
| DEV-04 | skill_examples/03_fully_guided/SKILL.md — exact commands, scripts, replacement list, rollback | P1 | M | Done |
| DEV-05 | dev_tools/scripts/clickhouse_introspect.py | P0 | S | Done |
| DEV-06 | dev_tools/scripts/chroma_patch.py | P0 | S | Done |
| DEV-07 | dev_tools/scripts/yaml_patch.py | P0 | S | Done |
| DEV-08 | dev_tools/scripts/prompt_patch.py | P0 | S | Done |
| DEV-09 | dev_tools/schema_sync.py — full CLI procedure composing all scripts | P0 | M | Done |
| DEV-10 | SchemaSyncReport dataclass with complete change log | P0 | S | Done |
| DEV-11 | --dry-run flag (shows what would change, touches nothing) | P1 | S | Done |
| DEV-12 | --rollback flag (reverses a previous sync) | P2 | S | Done |
| DEV-13 | dev_tools/README.md — explains progression from naive to fully guided | P0 | S | Done |
| DEV-14 | End-to-end: after schema_sync, agent returns correct rows in TUI | P0 | M | Done |

---

### Epic 5 — Tests (Core ✅ Done + Pending Suggestion)

**Test philosophy:** tests validate the *outcome* of applying a skill, not the skill code itself.
TST-07 and TST-08 are the **skill outcome contract** — regardless of which skill (or tool) was used,
these assertions must pass: YAML contains `merged_at`, prompts don't contain `merged = 1`,
ChromaDB has no stale chunks, and the agent returns correct rows.

| ID | Story | Priority | Estimate | Status |
|----|-------|----------|----------|--------|
| TST-01 | tests/conftest.py — mock ClickHouse + mock ChromaDB fixtures | P0 | M | Done |
| TST-02 | tests/fixtures/ — pre/post schema YAMLs + sample row JSON | P0 | S | Done |
| TST-03 | @pytest.mark.pre_migration — ghost contributor query returns rows | P0 | S | Done |
| TST-04 | @pytest.mark.pre_migration — RAG returns merged UInt8 context | P0 | S | Done |
| TST-05 | @pytest.mark.post_migration — query returns 0 rows after migration | P0 | S | Done |
| TST-06 | @pytest.mark.post_migration — RAG still returns stale merged chunk | P0 | S | Done |
| TST-07 | @pytest.mark.schema_sync — skill outcome: all 4 layers correctly patched (YAML, ChromaDB, NL2SQL prompt, RAG prompt) | P0 | M | Done |
| TST-08 | @pytest.mark.schema_sync — skill outcome: query returns correct rows after sync | P0 | S | Done |
| TST-09 | test_schema_sync.py — unit tests for each patch utility function | P1 | M | Done |
| TST-10 | test_agents.py — verify agent prompts contain correct field names pre/post sync | P1 | M | Done |
| TST-11 | CI: pytest -m "pre_migration or post_migration or schema_sync or complete_flow" in GitHub Actions | P1 | S | Done |
| TST-12 | Mocked complete flow: pre_migration → post_migration → schema_sync recovery for `kubernetes/kubernetes` | P1 | M | Done |
| TST-13 | Pending suggestion: schema upgrade gate profile (fails until full post-migration code readiness) | P2 | S | Pending |

---

### Epic 6 — Observability

| ID | Story | Priority | Estimate | Status |
|----|-------|----------|----------|--------|
| OBS-01 | loguru logger: file sink, stdout disabled, per-session log file | P0 | S | Done |
| OBS-02 | MLflow autolog applied to orchestrator, AgentRAG, AgentNL2SQL | P0 | S | Done |
| OBS-03 | MLflow run structure: root run → nested spans per sub-agent | P0 | M | Done |
| OBS-04 | MLflow experiment pre-created on container startup | P0 | S | Done |
| OBS-05 | TUI panel showing MLflow run URL for current query | P1 | S | Done |

---

### Epic 7 — Documentation

| ID | Story | Priority | Estimate | Status |
|----|-------|----------|----------|--------|
| DOC-01 | README.md quick start + Demo 01 section | P0 | S | Done |
| DOC-02 | agentic_system/README.md — architecture, memory, TUI, file map | P0 | S | Done |
| DOC-03 | docs/DEMO_SCRIPT.md — presenter guide for 3 acts | P0 | M | Done |
| DOC-04 | docs/DEV_TOOLS.md — skill progression guide | P0 | M | Done |
| DOC-05 | docs/ARCHITECTURE.md — AgentAsTools data flow | P1 | M | Done |
| DOC-06 | docs/SCHEMA_REFERENCE.md — GitHub Archive fields | P1 | S | Done |
| DOC-07 | docs/TROUBLESHOOTING.md — common issues | P1 | S | Done |

---

### Epic 8 — Improvements ✅ Done

Workshop reliability and offline-first improvements. Adds a controlled local dataset, a `LOCAL_SEED` agent mode, three bug fixes discovered during live verification, and expanded `AUDIENCE_GUIDE.md` documentation covering expected results per act and the `schema_upgrade_gate` test lifecycle.

| ID | Story | Priority | Estimate | Status |
|----|-------|----------|----------|--------|
| IMP-01 | Local dummy seed: `db/clickhouse/init/03_seed_local.sql` — 18 rows, 3 repos, ghost-contributor pattern | P1 | S | Done |
| IMP-02 | `make seed LOCAL=1` — Makefile parameter routing to local SQL file | P1 | S | Done |
| IMP-03 | Document `make seed LOCAL=1` offline fallback in AUDIENCE_GUIDE.md and README.md | P1 | S | Done |
| IMP-04 | Fix local seed reliability: remove inline comments from VALUES, stdin pipe, DROP+CREATE to clear ClickHouse mutation state | P0 | S | Done |
| IMP-05 | `LOCAL_SEED` agent mode: config flag, `LOCAL_DEMO_QUESTION`, TUI hints, NL2SQL/RAG prompt override blocks | P1 | M | Done |
| IMP-06 | Document per-act expected results (local dataset) and `schema_upgrade_gate` lifecycle in AUDIENCE_GUIDE.md | P1 | S | Done |

---

### Epic 9 — Nice to Have (Budget-Dependent)

| ID | Story | Priority | Estimate | Status |
|----|-------|----------|----------|--------|
| NTH-01 | Azure Container Apps: ClickHouse deployment | P3 | L | Pending |
| NTH-02 | Azure Container Apps: ChromaDB deployment | P3 | L | Pending |
| NTH-03 | Azure Container Apps: MLflow server deployment | P3 | M | Pending |
| NTH-04 | Azure infra-as-code: Bicep or Terraform | P3 | L | Pending |
| NTH-05 | Gradio Web UI variant (alternative to TUI, same agent backend) | P3 | M | Pending |
| NTH-06 | Azure Container Apps: Gradio Web UI deployment | P3 | M | Pending |
| NTH-07 | docs/AZURE_DEPLOY.md | P3 | M | Pending |

---

## 5. Technical Constraints

| Constraint | Decision |
|------------|----------|
| Python version | 3.14 (managed with `uv`) |
| Agentic framework | OpenAI Agents SDK — Agent, as_tool(), tool-calling loop |
| Agentic pattern | AgentAsTools — AgentRAG and AgentNL2SQL exposed as tools to root orchestrator |
| SQL database | ClickHouse (Docker, persistent volume) |
| Vector database | ChromaDB (Docker, persistent volume) |
| AI tracing | MLflow — mlflow.openai.autolog() |
| Application logging | loguru — file sink only, stdout disabled (Textual TUI owns stdout) |
| TUI framework | Textual |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | gpt-4o (configurable via .env, Azure OpenAI supported) |
| OS support | macOS (Apple Silicon + Intel), Linux |
| Schema migration | Field rename only: merged → merged_at |
| Dataset slice | ~5M rows filtered to PullRequestEvent |
| Tests | pytest with mocks — no live DB or LLM required |

---

## 6. Definition of Done

A demo is ready to present when:

- [x] `make up && make seed && make seed-vectors` completes without errors
- [x] `python agentic_system/main.py` launches TUI; logs go to file only, stdout clean
- [x] TUI query "ghost contributors on kubernetes/kubernetes" returns correct rows (Act 1)
- [x] Follow-up questions work with conversation memory (no need to re-specify context)
- [ ] MLflow UI at localhost:5000 shows nested spans with token counts per agent
- [x] `make migrate` causes silent wrong answer — 0 rows, no exception (Act 2 verified at SQL level)
- [x] `python dev_tools/schema_sync.py --table github_events` patches all 4 layers and prints report (Act 3)
- [x] Same TUI query returns correct rows after schema-sync (Act 3 complete)
- [ ] `make rollback` restores original schema; agent works again
- [x] `pytest -m "pre_migration or post_migration or schema_sync"` passes without live DB or LLM
- [ ] dev_tools/skill_examples/ contains all 4 progression examples, each with a README
- [ ] docs/DEMO_SCRIPT.md covers all 3 acts for a presenter
- [ ] Cold start completes in under 5 minutes

---

*End of Backlog v0.4*
