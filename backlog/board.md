# Backlog Board

_Generated from `/Users/mmartin/projects/skills_talk_agent_camp_2026/backlog` on 2026-04-09 21:32 UTC_

Status legend: `[ ] Todo`, `[~] In Progress`, `[x] Done`

| Task | Epic | Status | Short Description |
|------|------|--------|-------------------|
| INF-00 - Epic 1 Setup | Epic 1 - Infrastructure and Data | [x] Done | Establish Epic 1 scope, baseline structure, and traceability before implementation tasks. |
| INF-01 - ClickHouse Dockerfile and Persistent Volume | Epic 1 - Infrastructure and Data | [x] Done | Create the ClickHouse container baseline and persistence foundation for local demo data. |
| INF-02 - ClickHouse Init SQL for Pre-Migration Schema | Epic 1 - Infrastructure and Data | [x] Done | Define the initial github_events ClickHouse schema for the pre-migration state. |
| INF-03 - Seed Script for GitHub Archive Pull Request Sample | Epic 1 - Infrastructure and Data | [x] Done | Implement repeatable ClickHouse seeding for an approximately 5M-row pull request sample. |
| INF-04 - ChromaDB Dockerfile and Persistent Volume | Epic 1 - Infrastructure and Data | [x] Done | Create the ChromaDB container baseline with persistent storage for vector data. |
| INF-05 - ChromaDB Seed for Schema Docs and Q&A Examples | Epic 1 - Infrastructure and Data | [x] Done | Seed ChromaDB with schema context and Q&A examples for retrieval workflows. |
| INF-06 - MLflow Dockerfile and Tracking Server with SQLite Backend | Epic 1 - Infrastructure and Data | [x] Done | Create a local MLflow tracking baseline with SQLite backend and persistent artifacts. |
| INF-07 - docker-compose.yml Wiring for ClickHouse, ChromaDB, and MLflow | Epic 1 - Infrastructure and Data | [x] Done | Wire ClickHouse, ChromaDB, and MLflow into one local compose stack with persistence. |
| INF-08 - .env.example and Makefile with Required Infrastructure Targets | Epic 1 - Infrastructure and Data | [x] Done | Standardize infrastructure workflows with .env defaults and required Make targets. |
| INF-09 - Verify Cold-Start on macOS (Apple Silicon) | Epic 1 - Infrastructure and Data | [x] Done | Validate cold-start from clean state on macOS Apple Silicon using the standard make workflow. |
| INF-10 - Verify Cold-Start on Linux | Epic 1 - Infrastructure and Data | [x] Done | Validate cold-start from clean state on Linux using the standard make workflow. |
| AGT-01 - AgentRAG — Definition, System Prompt, Few-Shot Examples, vector_search Tool | Epic 2 - Agentic System (Act 1) | [x] Done | Build the AgentRAG sub-agent with its system prompt, few-shot examples, and ChromaDB vector_search tool. |
| AGT-02 - AgentNL2SQL — Definition, System Prompt, Few-Shot SQL Examples, run_sql Tool | Epic 2 - Agentic System (Act 1) | [x] Done | Build the AgentNL2SQL sub-agent with its system prompt, few-shot SQL examples, and ClickHouse run_sql tool. |
| AGT-03 - Root Orchestrator — Generic Agent[DemoContext] with Azure/OpenAI Setup | Epic 2 - Agentic System (Act 1) | [x] Done | Build the generic GitHub Archive orchestrator, OpenAI/Azure client setup, credentials models, and demo runner helper. |
| AGT-04 - agentic_system/schema/github_events.yaml — Machine-Readable Schema Definition | Epic 2 - Agentic System (Act 1) | [x] Done | Create the YAML schema definition file for github_events that agents and schema-sync reference as the authoritative field contract. |
| AGT-05 - Textual TUI — Input Panel, Answer Panel, Agent Trace Panel | Epic 2 - Agentic System (Act 1) | [x] Done | Build the Textual terminal UI with three panels for question input, answer display, and live agent trace output. |
| AGT-06 - loguru Setup — File Sink Only, stdout Disabled | Epic 2 - Agentic System (Act 1) | [x] Done | Configure loguru to write all logs to a rotating session file and remove the default stdout handler so the Textual TUI owns the terminal. |
| AGT-07 - MLflow Tracing via autolog and OpenAI Client Setup | Epic 2 - Agentic System (Act 1) | [x] Done | Configure mlflow.openai.autolog() and the provider-aware OpenAI client in agentic_system/setup.py so every agent run is traced automatically. |
| AGT-08 - agentic_system/main.py — Launches TUI and Wires Everything Together | Epic 2 - Agentic System (Act 1) | [x] Done | Create agentic_system/main.py as the single entry point that calls setup_openai(), activates loguru, and launches the Textual TUI. |
| AGT-09 - End-to-End — Ghost Contributor Query Returns Correct Rows | Epic 2 - Agentic System (Act 1) | [x] Done | Verify the full Act 1 demo path works end-to-end — the ghost contributor question produces correct SQL and non-empty results via the TUI. |
| AGT-10 - Conversation Memory — Session-Scoped History via to_input_list() | Epic 2 - Agentic System (Act 1) | [x] Done | Add session-scoped conversation memory to the TUI so the agent can answer follow-up questions with full prior context. |
| MIG-01 - scripts/migrate_schema.py — Rename merged → merged_at | Epic 3 - Migration Scripts (Act 2) | [x] Done | Implement the Act 2 schema migration that adds merged_at and zeros out merged, causing the agent to return silent wrong answers. |
| MIG-02 - Migration Marks ChromaDB Chunks Stale — Content Intentionally Left Wrong | Epic 3 - Migration Scripts (Act 2) | [x] Done | After the ClickHouse migration, mark migration-sensitive ChromaDB chunks as stale without fixing their content — leaving the RAG layer broken for Act 2. |
| MIG-03 - scripts/rollback_schema.py — Full Schema Rollback | Epic 3 - Migration Scripts (Act 2) | [x] Done | Implement the rollback script that restores the pre-migration schema in ClickHouse and clears stale metadata in ChromaDB. |
| MIG-04 - scripts/validate_schema.py — Diff Live DB vs YAML Contract | Epic 3 - Migration Scripts (Act 2) | [x] Done | Implement a standalone diagnostic that diffs the live ClickHouse schema against the YAML contract and reports drift. |
| MIG-05 - Verify Silent Wrong Answer After Migration | Epic 3 - Migration Scripts (Act 2) | [x] Done | Confirm that after migration the agent returns 0 rows with no exception — the intended Act 2 silent failure. |
| MIG-06 - Makefile Targets — make migrate, make rollback, make validate-schema | Epic 3 - Migration Scripts (Act 2) | [x] Done | Wire the migration, rollback, and validation scripts into Makefile targets so the presenter runs a single command during the demo. |
| DEV-01 - skill_examples/00_naive/SKILL.md — Naive Skill | Epic 4 - Developer Tools (Act 3) | [x] Done | Naive SKILL.md with no files listed and no procedure — just "something broke, fix it." Baseline for the skill progression that shows what happens when Claude... |
| DEV-02 - skill_examples/01_structured/SKILL.md — Structured Skill | Epic 4 - Developer Tools (Act 3) | [x] Done | Structured SKILL.md that lists the four files/systems to inspect and points to validate_schema.py |
| DEV-03 - skill_examples/02_agent_assisted/SKILL.md — Agent-Assisted Skill | Epic 4 - Developer Tools (Act 3) | [x] Done | Agent-assisted SKILL.md with a four-layer context table and a six-step repair sequence |
| DEV-04 - skill_examples/03_fully_guided/SKILL.md — Fully Guided Skill | Epic 4 - Developer Tools (Act 3) | [x] Done | Fully guided SKILL.md with one-command fix, step-by-step fallback with exact uv run commands, pre/post validation, rollback procedure, and a references/ dire... |
| DEV-05 - dev_tools/scripts/clickhouse_introspect.py | Epic 4 - Developer Tools (Act 3) | [x] Done | Introspects the live ClickHouse schema for a given table and returns {column: type} |
| DEV-06 - dev_tools/scripts/chroma_patch.py | Epic 4 - Developer Tools (Act 3) | [x] Done | Finds stale ChromaDB chunks (metadata.stale == True), applies text replacements to update their content for the post-migration schema, re-embeds with the sam... |
| DEV-07 - dev_tools/scripts/yaml_patch.py | Epic 4 - Developer Tools (Act 3) | [x] Done | Reads agentic_system/schema/<table>.yaml, diffs it against the live ClickHouse schema, adds missing columns, updates changed types and post-migration descrip... |
| DEV-08 - dev_tools/scripts/prompt_patch.py | Epic 4 - Developer Tools (Act 3) | [x] Done | Patches the NL2SQL and RAG system prompt .md files to replace pre-migration field references (merged UInt8, merged = 1) with post-migration equivalents (merg... |
| DEV-09 - dev_tools/schema_sync.py — Full CLI Composing All Patch Scripts | Epic 4 - Developer Tools (Act 3) | [x] Done | Main CLI that orchestrates clickhouse_introspect → yaml_patch → chroma_patch → prompt_patch in one pass |
| DEV-10 - SchemaSyncReport Dataclass with Complete Change Log | Epic 4 - Developer Tools (Act 3) | [x] Done | Dataclass in dev_tools/models.py capturing the complete change log from a schema_sync run — yaml_changes, chroma_changes, prompt_changes, live schema snapsho... |
| DEV-11 - --dry-run Flag for schema_sync.py | Epic 4 - Developer Tools (Act 3) | [x] Done | --dry-run flag that passes through all four patch scripts, shows every change that would be made, and touches nothing |
| DEV-12 - --rollback Flag for schema_sync.py | Epic 4 - Developer Tools (Act 3) | [x] Done | --rollback flag that reverses a previous schema_sync run by restoring the YAML contract and prompt files from saved snapshots |
| DEV-13 - dev_tools/README.md — Skill Progression Guide | Epic 4 - Developer Tools (Act 3) | [x] Done | README explaining the skill_examples/ progression from 00_naive to 03_fully_guided, documenting schema_sync.py usage, all script CLI flags, and the four laye... |
| DEV-14 - End-to-End — Agent Returns Correct Rows After schema_sync | Epic 4 - Developer Tools (Act 3) | [x] Done | Verify that after running schema_sync.py following make migrate, the ghost contributor question in the TUI returns correct (non-zero) rows, completing the Ac... |
| TST-01 - tests/conftest.py — Mock Fixtures | Epic 5 - Tests | [x] Done | Shared pytest fixtures providing mock ClickHouse and mock ChromaDB clients scoped to the pre-migration schema state |
| TST-02 - tests/fixtures/ — Pre/Post Schema YAMLs + Sample Row JSON | Epic 5 - Tests | [x] Done | Static fixture files — pre-migration and post-migration github_events.yaml snapshots plus a sample row JSON — used by schema_sync unit tests to validate patc... |
| TST-03 - test_use_case.py — @pre_migration — Ghost Contributor Query Returns Rows | Epic 5 - Tests | [x] Done | Pre-migration test verifying that the ghost contributor SQL uses `merged = 1` and returns non-empty rows via the mock ClickHouse client. |
| TST-04 - test_use_case.py — @pre_migration — RAG Returns merged UInt8 Context | Epic 5 - Tests | [x] Done | Pre-migration test verifying that the RAG tool returns context containing `merged` and `UInt8`, and does not return `merged_at`. |
| TST-05 - test_use_case.py — @post_migration — Query Returns 0 Rows After Migration | Epic 5 - Tests | [x] Done | Post-migration test verifying the silent failure: the same ghost contributor SQL with `merged = 1` returns 0 rows after `make migrate`, with no exception thr... |
| TST-06 - test_use_case.py — @post_migration — RAG Still Returns Stale merged Chunk | Epic 5 - Tests | [x] Done | Post-migration test verifying that the RAG tool still returns the stale `merged UInt8` chunk before schema_sync has run — showing the second layer of the sil... |
| TST-07 - test_schema_sync.py — @schema_sync — Skill Outcome: All 4 Layers Patched | Epic 5 - Tests | [x] Done | Skill outcome contract test |
| TST-08 - test_schema_sync.py — @schema_sync — Skill Outcome: Query Returns Correct Rows | Epic 5 - Tests | [x] Done | Skill outcome contract test |
| TST-09 - test_schema_sync.py — Unit Tests for Each Patch Utility Function | Epic 5 - Tests | [x] Done | Unit tests for yaml_patch.patch(), chroma_patch.patch(), and prompt_patch.patch() using fixture files and mock clients |
| TST-10 - test_agents.py — Agent Prompt Field Names Pre/Post Sync | Epic 5 - Tests | [x] Done | Validates prompt-layer behavior for pre-migration baseline and schema-sync patch output, without requiring live services. |
| TST-11 - CI — pytest GitHub Actions Workflow | Epic 5 - Tests | [x] Done | GitHub Actions workflow running `pytest -m "pre_migration or post_migration or schema_sync or complete_flow"` without live DB or LLM |
| TST-12 - Mocked Complete Flow — pre_migration → post_migration → schema_sync Recovery | Epic 5 - Tests | [x] Done | Stateful mocked end-to-end test for the Kubernetes ghost-contributors question proving the full lifecycle: pre works, post-migration silently fails, and full... |
| TST-13 - Schema Upgrade Gate — Explicit Post-Migration Readiness Check | Epic 5 - Tests | [x] Done | Pending suggestion |
| OBS-03 - MLflow Run Structure — Root Run With Nested Agent Spans | Epic 6 - Observability | [x] Done | Ensure each query creates a root MLflow run so nested agent/tool spans attach to a single parent run. |
| OBS-04 - MLflow Experiment Pre-Created on Container Startup | Epic 6 - Observability | [x] Done | Ensure the configured MLflow experiment exists as soon as the MLflow container starts. |
| OBS-05 - TUI Panel Showing MLflow Run URL | Epic 6 - Observability | [x] Done | Display the MLflow run link for the current query directly in the Textual TUI. |
| DOC-01 - Epic 7 — Workshop Documentation Suite | Epic 7 - Documentation | [x] Done | Create AUDIENCE_GUIDE.md as a full PDF-grade workshop guide and update README.md to reference it. |
| IMP-01 - Local Dummy Seed Data for Workshop Fallback | Epic 8 - Improvements | [x] Done | Create a controlled local seed file with 10–20 rows across 2–3 repos so workshops can run without network access to GitHub Archive. |
| IMP-02 - make seed LOCAL=1 Makefile Parameter | Epic 8 - Improvements | [x] Done | Add LOCAL parameter to make seed so presenters can load the controlled 10–20 row dataset instead of pulling from GitHub Archive. |
| IMP-03 - Document Local Seed Mode in AUDIENCE_GUIDE and README | Epic 8 - Improvements | [x] Done | Update AUDIENCE_GUIDE.md and README.md to document the make seed LOCAL=1 offline fallback for workshop environments. |
| IMP-04 - Fix Local Seed Reliability — Comments, Pipe, and Mutation State | Epic 8 - Improvements | [x] Done | Fix three bugs that silently prevented make seed LOCAL=1 from loading correct data into ClickHouse. |
| IMP-05 - LOCAL_SEED Agent Mode — Config, Demo Routing, TUI Hints, Prompt Overrides | Epic 8 - Improvements | [x] Done | Add LOCAL_SEED env flag that routes the demo question, TUI hints, and agent prompt context to match the 18-row local dataset. |
| IMP-06 - Document Local Seed Expected Results and Schema Upgrade Gate in AUDIENCE_GUIDE | Epic 8 - Improvements | [x] Done | Add verified per-act expected query results for the local dataset and document the schema_upgrade_gate test in AUDIENCE_GUIDE.md. |

## Usage

```bash
python3 scripts/backlog_board.py
python3 scripts/backlog_board.py --format json
python3 scripts/backlog_board.py --write-board
```
