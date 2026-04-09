"""
tests/test_use_case.py

Phase 1 acceptance tests — pre-migration schema state.

Run with:
    pytest -m pre_migration

These tests verify that:
  - The ghost contributor SQL uses merged = 1 (pre-migration predicate).
  - The RAG tool returns context with 'merged' and 'UInt8', never 'merged_at'.

External services (ClickHouse, ChromaDB) are replaced by fixtures in conftest.py.
"""

import json

import pytest
from unittest.mock import patch

from agentic_system.agents_core.nl2sql.tools.run_sql import run_sql_core
from agentic_system.agents_core.rag.tools.vector_search import vector_search_core


GHOST_CONTRIBUTOR_SQL = """
SELECT
    repo_name,
    actor_login,
    countIf(action = 'opened')                    AS prs_opened,
    countIf(action = 'closed' AND merged = 1)     AS prs_merged
FROM github_events
WHERE event_type = 'PullRequestEvent'
GROUP BY repo_name, actor_login
HAVING prs_opened > 0 AND prs_merged = 0
ORDER BY prs_opened DESC
LIMIT 50
""".strip()


@pytest.mark.pre_migration
def test_ghost_contributor_query_pre_migration(mock_clickhouse_client):
    """Ghost contributor SQL uses merged = 1 and returns non-empty rows."""
    with patch(
        "agentic_system.agents_core.nl2sql.tools.run_sql._get_client",
        return_value=mock_clickhouse_client,
    ):
        result_json = run_sql_core(GHOST_CONTRIBUTOR_SQL)

    result = json.loads(result_json)

    assert result.get("error") is None, f"Unexpected error: {result.get('error')}"
    assert "merged = 1" in GHOST_CONTRIBUTOR_SQL
    assert result["row_count"] > 0
    assert len(result["rows"]) > 0
    assert result["rows"][0]["repo_name"] == "kubernetes/kubernetes"


@pytest.mark.pre_migration
def test_rag_returns_correct_field_pre_migration(mock_chroma_client):
    """RAG context contains 'merged' and 'UInt8', not 'merged_at'."""
    with patch(
        "agentic_system.agents_core.rag.tools.vector_search._get_client",
        return_value=mock_chroma_client,
    ):
        context = vector_search_core("ghost contributors merged PR")

    assert "merged" in context, "Expected 'merged' in RAG context"
    assert "UInt8" in context, "Expected 'UInt8' in RAG context"
    assert "merged_at" not in context, "Did not expect 'merged_at' in pre-migration RAG context"


@pytest.mark.post_migration
def test_ghost_contributor_query_post_migration(mock_clickhouse_client_post_migration):
    """After migration, legacy merged=1 SQL should return zero rows silently."""
    with patch(
        "agentic_system.agents_core.nl2sql.tools.run_sql._get_client",
        return_value=mock_clickhouse_client_post_migration,
    ):
        result_json = run_sql_core(GHOST_CONTRIBUTOR_SQL)

    result = json.loads(result_json)
    assert result.get("error") is None, f"Unexpected error: {result.get('error')}"
    assert "merged = 1" in GHOST_CONTRIBUTOR_SQL
    assert result["row_count"] == 0
    assert result["rows"] == []


@pytest.mark.post_migration
def test_rag_returns_stale_merged_chunk_post_migration(mock_chroma_client_post_migration):
    """After migration but before sync, RAG still returns stale merged UInt8 context."""
    with patch(
        "agentic_system.agents_core.rag.tools.vector_search._get_client",
        return_value=mock_chroma_client_post_migration,
    ):
        context = vector_search_core("ghost contributors merged PR")

    assert "merged" in context, "Expected stale 'merged' field in RAG context"
    assert "UInt8" in context, "Expected stale 'UInt8' type in RAG context"
    assert "merged = 1" in context, "Expected stale SQL predicate in RAG context"
    assert "merged_at" not in context, "Did not expect post-sync field before schema_sync"
