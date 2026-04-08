"""
Mocked complete flow test (stateful):
pre-migration -> migration (silent failure) -> schema_sync (fully guided fix) -> recovered.

This test intentionally simulates the full lifecycle with:
- specific question: kubernetes/kubernetes ghost contributors
- mocked agent API SQL generation
- mocked ClickHouse and ChromaDB backends
- real patch utilities invoked through schema_sync.sync()
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from agentic_system.agents_core.nl2sql.tools.run_sql import run_sql_core
from agentic_system.agents_core.rag.tools.vector_search import vector_search_core
from dev_tools import schema_sync
from dev_tools.scripts import chroma_patch, clickhouse_introspect, prompt_patch, yaml_patch


ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "tests" / "fixtures"

QUESTION = "Show me ghost contributors on kubernetes/kubernetes"


class _FakeQueryResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def named_results(self):
        return self._rows


class _PhaseClickHouseClient:
    """In-memory ClickHouse behavior across lifecycle phases."""

    def __init__(self) -> None:
        self.phase = "pre_migration"

    def query(self, sql: str) -> _FakeQueryResult:
        pre_rows = [
            {
                "repo_name": "kubernetes/kubernetes",
                "actor_login": "ghost_user1",
                "prs_opened": 5,
                "prs_merged": 0,
            },
            {
                "repo_name": "kubernetes/kubernetes",
                "actor_login": "ghost_user2",
                "prs_opened": 3,
                "prs_merged": 0,
            },
        ]

        # Pre-migration behavior: legacy merged predicate works.
        if self.phase == "pre_migration" and "merged = 1" in sql:
            return _FakeQueryResult(pre_rows)

        # Post-migration behavior: legacy predicate silently returns 0 rows.
        if self.phase in {"post_migration", "post_sync"} and "merged = 1" in sql:
            return _FakeQueryResult([])

        # Post-sync behavior: updated predicate works on migrated schema.
        if self.phase == "post_sync" and "merged_at IS NOT NULL" in sql:
            return _FakeQueryResult(pre_rows)

        return _FakeQueryResult([])


class _FakeCollection:
    def __init__(self, docs: list[str]) -> None:
        self._docs = docs

    def query(self, query_embeddings: list[list[float]], n_results: int) -> dict[str, list[list[str]]]:
        del query_embeddings
        return {"documents": [self._docs[:n_results]]}


class _FakeChromaClient:
    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store

    def get_collection(self, name: str) -> _FakeCollection:
        if name == "schema_docs":
            return _FakeCollection(self._store["schema_docs_id"]["documents"])
        if name == "qa_examples":
            return _FakeCollection(self._store["qa_examples_id"]["documents"])
        return _FakeCollection([])


def _mock_api_generate_sql(question: str, context: str, nl2sql_prompt_text: str) -> str:
    """Deterministic fake of NL2SQL API behavior based on prompt + retrieved context."""
    del question
    use_post_migration_predicate = (
        "merged_at IS NOT NULL" in nl2sql_prompt_text and "merged_at" in context
    )
    merged_predicate = "merged_at IS NOT NULL" if use_post_migration_predicate else "merged = 1"

    return f"""
SELECT
    repo_name,
    actor_login,
    countIf(action = 'opened') AS prs_opened,
    countIf(action = 'closed' AND {merged_predicate}) AS prs_merged
FROM github_events
WHERE event_type = 'PullRequestEvent'
  AND repo_name = 'kubernetes/kubernetes'
GROUP BY repo_name, actor_login
HAVING prs_opened > 0 AND prs_merged = 0
ORDER BY prs_opened DESC
LIMIT 50
""".strip()


def _setup_mock_chroma_http(monkeypatch: pytest.MonkeyPatch, store: dict[str, dict[str, Any]]) -> None:
    collections = [
        {"id": "schema_docs_id", "name": "schema_docs"},
        {"id": "qa_examples_id", "name": "qa_examples"},
    ]

    def _list_collections() -> list[dict]:
        return collections

    def _get_all_items(collection_id: str) -> dict:
        return store[collection_id]

    def _upsert(
        collection_id: str,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        existing = store[collection_id]
        id_to_index = {item_id: i for i, item_id in enumerate(existing["ids"])}
        for i, item_id in enumerate(ids):
            idx = id_to_index[item_id]
            existing["documents"][idx] = documents[i]
            existing["metadatas"][idx] = metadatas[i]

    monkeypatch.setattr(chroma_patch, "_list_collections", _list_collections)
    monkeypatch.setattr(chroma_patch, "_get_all_items", _get_all_items)
    monkeypatch.setattr(chroma_patch, "_upsert", _upsert)


def _ask_agent_like(
    question: str,
    nl2sql_prompt_path: Path,
    clickhouse_client: _PhaseClickHouseClient,
    chroma_store: dict[str, dict[str, Any]],
) -> tuple[str, str, dict[str, Any]]:
    with patch(
        "agentic_system.agents_core.rag.tools.vector_search._get_client",
        return_value=_FakeChromaClient(chroma_store),
    ):
        context = vector_search_core(question)

    prompt_text = nl2sql_prompt_path.read_text(encoding="utf-8")
    sql = _mock_api_generate_sql(question, context, prompt_text)

    with patch(
        "agentic_system.agents_core.nl2sql.tools.run_sql._get_client",
        return_value=clickhouse_client,
    ):
        result_json = run_sql_core(sql)

    return sql, context, json.loads(result_json)


@pytest.mark.schema_sync
@pytest.mark.complete_flow
def test_mocked_complete_flow_kubernetes_question(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    End-to-end mocked lifecycle assertion:
    1) pre-migration query works
    2) post-migration query silently fails (0 rows)
    3) run fully guided fix (schema_sync)
    4) same query works again
    """

    temp_dir = ROOT / "tests" / ".tmp_complete_flow" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ---- Arrange pre-migration file state used by schema_sync patchers ----
        schema_dir = temp_dir / "schema"
        schema_dir.mkdir(parents=True, exist_ok=True)
        schema_file = schema_dir / "github_events.yaml"
        schema_file.write_text(
            (FIXTURES_DIR / "github_events_pre_migration.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        nl2sql_prompt = temp_dir / "nl2sql_system.md"
        rag_prompt = temp_dir / "rag_system.md"
        prompt_seed = (
            "| merged | UInt8 | pre-migration merge flag |\n"
            "Use `merged = 1` for merged PRs and `merged = 0` for unmerged (pre-migration).\n"
        )
        nl2sql_prompt.write_text(prompt_seed, encoding="utf-8")
        rag_prompt.write_text(prompt_seed, encoding="utf-8")

        # ---- Arrange Chroma store in stale post-migration content style ----
        chroma_store: dict[str, dict[str, Any]] = {
            "schema_docs_id": {
                "ids": ["schema_chunk_1"],
                "documents": [
                    "Field merged UInt8. Use merged = 1 to identify merged pull requests. State: pre-migration"
                ],
                "metadatas": [{"migration_sensitive": True, "stale": False, "schema_state": "pre_migration"}],
            },
            "qa_examples_id": {
                "ids": ["qa_chunk_1"],
                "documents": [
                    "SELECT countIf(action='closed' AND merged = 1) AS prs_merged FROM github_events"
                ],
                "metadatas": [{"migration_sensitive": True, "stale": False, "schema_state": "pre_migration"}],
            },
        }

        clickhouse_client = _PhaseClickHouseClient()

        # ---- Step 1: pre-migration works ----
        sql_pre, context_pre, result_pre = _ask_agent_like(
            QUESTION,
            nl2sql_prompt,
            clickhouse_client,
            chroma_store,
        )
        assert "merged = 1" in sql_pre
        assert "merged" in context_pre
        assert result_pre.get("error") is None
        assert result_pre["row_count"] > 0

        # ---- Step 2: simulate migrate -> silent failure ----
        clickhouse_client.phase = "post_migration"
        for collection in chroma_store.values():
            for meta in collection["metadatas"]:
                if meta.get("migration_sensitive"):
                    meta["stale"] = True
                    meta["schema_state"] = "post_migration_stale"

        sql_post, context_post, result_post = _ask_agent_like(
            QUESTION,
            nl2sql_prompt,
            clickhouse_client,
            chroma_store,
        )
        assert "merged = 1" in sql_post
        assert "merged = 1" in context_post
        assert result_post.get("error") is None
        assert result_post["row_count"] == 0

        # ---- Step 3: run fully guided fix path (schema_sync) ----
        _setup_mock_chroma_http(monkeypatch, chroma_store)
        monkeypatch.setattr(yaml_patch, "SCHEMA_DIR", schema_dir)
        monkeypatch.setattr(prompt_patch, "PROMPT_FILES", [nl2sql_prompt, rag_prompt])
        post_live_cols = {
            "event_type": "String",
            "action": "LowCardinality(String)",
            "actor_login": "String",
            "repo_name": "String",
            "created_at": "DateTime",
            "merged": "UInt8",
            "number": "UInt32",
            "title": "String",
            "merged_at": "Nullable(DateTime)",
        }
        monkeypatch.setattr(clickhouse_introspect, "introspect", lambda _table: post_live_cols)
        monkeypatch.setattr(schema_sync, "_save_rollback_state", lambda _table, _state: None)

        report = schema_sync.sync("github_events", dry_run=False)
        assert report.errors == []
        assert report.yaml_changes
        assert report.chroma_changes
        assert report.prompt_changes

        # ---- Step 4: same question succeeds after sync ----
        clickhouse_client.phase = "post_sync"
        sql_fixed, context_fixed, result_fixed = _ask_agent_like(
            QUESTION,
            nl2sql_prompt,
            clickhouse_client,
            chroma_store,
        )
        assert "merged_at IS NOT NULL" in sql_fixed
        assert "merged_at" in context_fixed
        assert "merged = 1" not in context_fixed
        assert result_fixed.get("error") is None
        assert result_fixed["row_count"] > 0

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
