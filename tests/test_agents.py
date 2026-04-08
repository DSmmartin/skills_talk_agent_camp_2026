"""
tests/test_agents.py

Prompt-layer regression checks for pre-migration and post-sync states.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from dev_tools.scripts import prompt_patch


ROOT = Path(__file__).resolve().parents[1]
NL2SQL_PROMPT = ROOT / "agentic_system" / "agents_core" / "nl2sql" / "prompts" / "system.md"
RAG_PROMPT = ROOT / "agentic_system" / "agents_core" / "rag" / "prompts" / "system.md"


def _write_pre_migration_prompt(path: Path) -> None:
    path.write_text(
        """
# Prompt
| merged | UInt8 | pre-migration merge flag |
Use `merged = 1` for merged PRs and `merged = 0` for unmerged (pre-migration).
""".strip()
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.pre_migration
def test_nl2sql_prompt_contains_pre_migration_field_names() -> None:
    content = NL2SQL_PROMPT.read_text(encoding="utf-8")

    assert "merged" in content
    assert "UInt8" in content
    assert "merged = 1" in content


@pytest.mark.pre_migration
def test_rag_prompt_baseline_pre_migration() -> None:
    content = RAG_PROMPT.read_text(encoding="utf-8")

    assert "github_events" in content
    assert "merged_at IS NOT NULL" not in content


@pytest.mark.schema_sync
def test_prompt_field_names_after_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_dir = ROOT / "tests" / ".tmp_prompts" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    nl2sql_prompt = temp_dir / "nl2sql_system.md"
    rag_prompt = temp_dir / "rag_system.md"

    try:
        _write_pre_migration_prompt(nl2sql_prompt)
        _write_pre_migration_prompt(rag_prompt)
        monkeypatch.setattr(prompt_patch, "PROMPT_FILES", [nl2sql_prompt, rag_prompt])

        changes = prompt_patch.patch(dry_run=False)
        assert changes

        nl2sql_content = nl2sql_prompt.read_text(encoding="utf-8")
        rag_content = rag_prompt.read_text(encoding="utf-8")

        assert "merged = 1" not in nl2sql_content
        assert "merged_at" in nl2sql_content

        assert "merged = 1" not in rag_content
        assert "merged_at" in rag_content
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
