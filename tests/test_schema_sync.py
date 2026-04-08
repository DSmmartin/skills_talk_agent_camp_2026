"""
tests/test_schema_sync.py

Epic 5 tests for schema-sync outcome contracts and utility-level patch behavior.
All tests run with mocks/temp files only (no live ClickHouse/ChromaDB/LLM).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
import yaml

from agentic_system.agents_core.nl2sql.tools.run_sql import run_sql_core
from dev_tools import schema_sync
from dev_tools.scripts import chroma_patch, clickhouse_introspect, prompt_patch, yaml_patch


pytestmark = pytest.mark.schema_sync

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "tests" / "fixtures"


def _load_yaml_columns(path: Path) -> dict[str, str]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {col["name"]: col["type"] for col in doc["columns"]}


def _write_pre_migration_prompt(path: Path) -> None:
    path.write_text(
        """
# Prompt
| merged | UInt8 | pre-migration merge flag |
Use `merged = 1` for merged PRs and `merged = 0` for unmerged (pre-migration).
Example: countIf(action = 'closed' AND merged = 1) AS merged_count
""".strip()
        + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def post_migration_live_cols() -> dict[str, str]:
    return _load_yaml_columns(FIXTURES_DIR / "github_events_post_migration.yaml")


@pytest.fixture
def temp_schema_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_file = schema_dir / "github_events.yaml"
    schema_file.write_text(
        (FIXTURES_DIR / "github_events_pre_migration.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(yaml_patch, "SCHEMA_DIR", schema_dir)
    return schema_file


@pytest.fixture
def temp_prompt_files(monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    temp_dir = ROOT / "tests" / ".tmp_prompts" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)

    nl2sql_prompt = temp_dir / "nl2sql_system.md"
    rag_prompt = temp_dir / "rag_system.md"
    _write_pre_migration_prompt(nl2sql_prompt)
    _write_pre_migration_prompt(rag_prompt)
    monkeypatch.setattr(prompt_patch, "PROMPT_FILES", [nl2sql_prompt, rag_prompt])
    try:
        yield {"nl2sql": nl2sql_prompt, "rag": rag_prompt}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def fake_chroma_store(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    collections = [
        {"id": "schema_docs_id", "name": "schema_docs"},
        {"id": "qa_examples_id", "name": "qa_examples"},
    ]
    store = {
        "schema_docs_id": {
            "ids": ["schema_chunk_1"],
            "documents": [
                "Field merged UInt8. Use merged = 1 to identify merged pull requests. State: pre-migration"
            ],
            "metadatas": [{"stale": True, "migration_sensitive": True}],
        },
        "qa_examples_id": {
            "ids": ["qa_chunk_1"],
            "documents": ["SELECT countIf(action='closed' AND merged = 1) AS merged_count"],
            "metadatas": [{"stale": True, "migration_sensitive": True}],
        },
    }
    upserts: list[dict[str, Any]] = []

    def _list_collections() -> list[dict]:
        return collections

    def _get_all_items(collection_id: str) -> dict:
        return store[collection_id]

    def _upsert(collection_id: str, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
        upserts.append(
            {
                "collection_id": collection_id,
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
            }
        )
        existing = store[collection_id]
        id_to_index = {item_id: i for i, item_id in enumerate(existing["ids"])}
        for i, item_id in enumerate(ids):
            idx = id_to_index[item_id]
            existing["documents"][idx] = documents[i]
            existing["metadatas"][idx] = metadatas[i]

    monkeypatch.setattr(chroma_patch, "_list_collections", _list_collections)
    monkeypatch.setattr(chroma_patch, "_get_all_items", _get_all_items)
    monkeypatch.setattr(chroma_patch, "_upsert", _upsert)

    return {"store": store, "upserts": upserts}


def test_all_four_layers_patched(
    monkeypatch: pytest.MonkeyPatch,
    post_migration_live_cols: dict[str, str],
    temp_schema_contract: Path,
    temp_prompt_files: dict[str, Path],
    fake_chroma_store: dict[str, Any],
) -> None:
    """TST-07: schema_sync patches YAML, Chroma, and prompts together."""
    monkeypatch.setattr(clickhouse_introspect, "introspect", lambda _table: post_migration_live_cols)
    monkeypatch.setattr(schema_sync, "_save_rollback_state", lambda _table, _state: None)

    report = schema_sync.sync("github_events", dry_run=False)

    assert report.errors == []
    assert report.yaml_changes, "Expected YAML contract changes"
    assert report.chroma_changes, "Expected ChromaDB changes"
    assert report.prompt_changes, "Expected prompt changes"

    yaml_doc = yaml.safe_load(temp_schema_contract.read_text(encoding="utf-8"))
    cols = {col["name"]: col for col in yaml_doc["columns"]}
    assert cols["merged_at"]["type"] == "Nullable(DateTime)"

    for prompt_path in temp_prompt_files.values():
        content = prompt_path.read_text(encoding="utf-8")
        assert "merged = 1" not in content
        assert "merged_at IS NOT NULL" in content

    for collection in fake_chroma_store["store"].values():
        assert collection["documents"], "Expected patched documents"
        assert collection["metadatas"], "Expected patched metadata"
        for doc in collection["documents"]:
            assert "merged = 1" not in doc
            assert "merged_at IS NOT NULL" in doc
        for metadata in collection["metadatas"]:
            assert metadata["stale"] is False
            assert metadata["schema_state"] == "post_migration_synced"


def test_query_returns_correct_rows_after_sync(
    mock_clickhouse_client_post_sync,
    temp_prompt_files: dict[str, Path],
) -> None:
    """TST-08: post-sync SQL with merged_at predicate returns non-empty rows."""
    changes = prompt_patch.patch(dry_run=False)
    assert changes

    prompt_text = temp_prompt_files["nl2sql"].read_text(encoding="utf-8")
    assert "merged = 1" not in prompt_text
    assert "merged_at IS NOT NULL" in prompt_text

    post_sync_sql = """
    SELECT
        repo_name,
        actor_login,
        countIf(action = 'opened') AS prs_opened,
        countIf(action = 'closed' AND merged_at IS NOT NULL) AS prs_merged
    FROM github_events
    WHERE event_type = 'PullRequestEvent'
    GROUP BY repo_name, actor_login
    HAVING prs_opened > 0 AND prs_merged = 0
    ORDER BY prs_opened DESC
    LIMIT 50
    """.strip()

    with patch(
        "agentic_system.agents_core.nl2sql.tools.run_sql._get_client",
        return_value=mock_clickhouse_client_post_sync,
    ):
        result_json = run_sql_core(post_sync_sql)

    result = json.loads(result_json)
    assert result.get("error") is None
    assert "merged_at IS NOT NULL" in post_sync_sql
    assert result["row_count"] > 0


def test_yaml_patch_updates_contract(
    temp_schema_contract: Path,
    post_migration_live_cols: dict[str, str],
) -> None:
    """TST-09: yaml_patch adds merged_at and updates migration-sensitive descriptions."""
    changes = yaml_patch.patch("github_events", post_migration_live_cols, dry_run=False)

    assert changes
    assert any(c.action == "added" and c.column == "merged_at" for c in changes)

    patched = yaml.safe_load(temp_schema_contract.read_text(encoding="utf-8"))
    patched_cols = {col["name"]: col["type"] for col in patched["columns"]}
    assert patched_cols["merged_at"] == "Nullable(DateTime)"
    assert patched["schema_state"] == "post_migration_synced"


def test_yaml_patch_dry_run_does_not_write(
    temp_schema_contract: Path,
    post_migration_live_cols: dict[str, str],
) -> None:
    """TST-09: yaml_patch dry-run reports changes without writing files."""
    before = temp_schema_contract.read_text(encoding="utf-8")

    changes = yaml_patch.patch("github_events", post_migration_live_cols, dry_run=True)

    after = temp_schema_contract.read_text(encoding="utf-8")
    assert changes
    assert before == after


def test_chroma_patch_updates_stale_chunks(fake_chroma_store: dict[str, Any]) -> None:
    """TST-09: chroma_patch updates stale docs + metadata and upserts changes."""
    changes = chroma_patch.patch(dry_run=False)

    assert changes
    assert fake_chroma_store["upserts"], "Expected upsert call in non-dry-run mode"
    for upsert in fake_chroma_store["upserts"]:
        for document in upsert["documents"]:
            assert "merged = 1" not in document
            assert "merged_at IS NOT NULL" in document
        for metadata in upsert["metadatas"]:
            assert metadata["stale"] is False
            assert metadata["schema_state"] == "post_migration_synced"


def test_chroma_patch_dry_run_does_not_upsert(fake_chroma_store: dict[str, Any]) -> None:
    """TST-09: chroma_patch dry-run reports changes and does not call upsert."""
    changes = chroma_patch.patch(dry_run=True)

    assert changes
    assert fake_chroma_store["upserts"] == []


def test_prompt_patch_updates_files(temp_prompt_files: dict[str, Path]) -> None:
    """TST-09: prompt_patch replaces pre-migration field references."""
    changes = prompt_patch.patch(dry_run=False)

    assert changes
    for prompt_path in temp_prompt_files.values():
        content = prompt_path.read_text(encoding="utf-8")
        assert "merged = 1" not in content
        assert "merged_at IS NOT NULL" in content


def test_prompt_patch_dry_run_does_not_write(temp_prompt_files: dict[str, Path]) -> None:
    """TST-09: prompt_patch dry-run reports changes and preserves file contents."""
    before = {k: p.read_text(encoding="utf-8") for k, p in temp_prompt_files.items()}

    changes = prompt_patch.patch(dry_run=True)

    after = {k: p.read_text(encoding="utf-8") for k, p in temp_prompt_files.items()}
    assert changes
    assert before == after
