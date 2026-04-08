"""
tests/conftest.py

Shared fixtures for the Ghost Contributors test suite.

Mocks are scoped to mirror the pre-migration schema state (merged UInt8).
All fixtures replace external service clients so tests run without live
ClickHouse, ChromaDB, or OpenAI connections.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_clickhouse_client():
    """ClickHouse client returning pre-migration ghost contributor rows."""
    rows = [
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
    query_result = MagicMock()
    query_result.named_results.return_value = rows

    client = MagicMock()
    client.query.return_value = query_result
    return client


@pytest.fixture
def mock_chroma_client():
    """ChromaDB client returning pre-migration schema context chunks."""
    schema_chunk = (
        "Field: merged\n"
        "Type: UInt8\n"
        "Description: 1 if the pull request was merged, 0 otherwise.\n"
        "Use merged = 1 to filter merged PRs and merged = 0 for unmerged PRs."
    )
    qa_chunk = (
        "Q: How do I find ghost contributors?\n"
        "A: SELECT repo_name, actor_login, countIf(action='opened') AS prs_opened, "
        "countIf(action='closed' AND merged = 1) AS prs_merged "
        "FROM github_events WHERE event_type = 'PullRequestEvent' "
        "GROUP BY repo_name, actor_login HAVING prs_opened > 0 AND prs_merged = 0"
    )

    def _get_collection(name: str) -> MagicMock:
        col = MagicMock()
        docs = [schema_chunk] if name == "schema_docs" else [qa_chunk]
        col.query.return_value = {"documents": [docs]}
        return col

    client = MagicMock()
    client.get_collection.side_effect = _get_collection
    return client


@pytest.fixture
def mock_clickhouse_client_post_migration():
    """ClickHouse client simulating post-migration silent wrong answer."""
    query_result = MagicMock()
    query_result.named_results.return_value = []

    client = MagicMock()
    client.query.return_value = query_result
    return client


@pytest.fixture
def mock_chroma_client_post_migration():
    """ChromaDB client returning stale pre-migration chunks after migration."""
    schema_chunk = (
        "Field: merged\n"
        "Type: UInt8\n"
        "Description: pre-migration merge flag where 1 means merged and 0 means not merged.\n"
        "Use merged = 1 for merged PRs."
    )
    qa_chunk = (
        "Q: How do I find merged pull requests?\n"
        "A: SELECT * FROM github_events WHERE merged = 1\n"
        "State: pre-migration"
    )

    def _get_collection(name: str) -> MagicMock:
        col = MagicMock()
        docs = [schema_chunk] if name == "schema_docs" else [qa_chunk]
        col.query.return_value = {"documents": [docs]}
        return col

    client = MagicMock()
    client.get_collection.side_effect = _get_collection
    return client


@pytest.fixture
def mock_clickhouse_client_post_sync():
    """ClickHouse client simulating corrected post-sync SQL output."""
    rows = [
        {
            "repo_name": "kubernetes/kubernetes",
            "actor_login": "ghost_user1",
            "prs_opened": 5,
            "prs_merged": 0,
        },
        {
            "repo_name": "kubernetes/kubernetes",
            "actor_login": "ghost_user2",
            "prs_opened": 4,
            "prs_merged": 0,
        },
    ]
    query_result = MagicMock()
    query_result.named_results.return_value = rows

    client = MagicMock()
    client.query.return_value = query_result
    return client
