"""
Hard gate for post-migration code readiness.

This test is intentionally strict: it fails unless repository files are already
updated for the post-migration schema (`merged_at`).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT / "agentic_system" / "schema" / "github_events.yaml"
NL2SQL_PROMPT = ROOT / "agentic_system" / "agents_core" / "nl2sql" / "prompts" / "system.md"
RAG_PROMPT = ROOT / "agentic_system" / "agents_core" / "rag" / "prompts" / "system.md"
NL2SQL_AGENT_DEF = ROOT / "agentic_system" / "agents_core" / "nl2sql" / "agent.py"


@pytest.mark.schema_upgrade_gate
def test_repo_code_is_upgraded_for_post_migration_schema() -> None:
    """
    Fails until code/files are migrated from legacy `merged` usage to `merged_at`.
    """
    failures: list[str] = []

    schema_doc = yaml.safe_load(SCHEMA_FILE.read_text(encoding="utf-8"))
    cols = {col["name"]: col for col in schema_doc.get("columns", [])}

    if "merged_at" not in cols:
        failures.append("Schema contract missing `merged_at` column.")
    else:
        merged_at_type = cols["merged_at"].get("type")
        if merged_at_type != "Nullable(DateTime)":
            failures.append(
                f"`merged_at` has wrong type: {merged_at_type!r} (expected 'Nullable(DateTime)')."
            )

    merged_desc = (cols.get("merged", {}) or {}).get("description", "")
    if "merged = 1" in merged_desc:
        failures.append("Schema contract still documents legacy predicate `merged = 1`.")

    nl2sql_prompt_text = NL2SQL_PROMPT.read_text(encoding="utf-8")
    if "merged = 1" in nl2sql_prompt_text:
        failures.append("NL2SQL prompt still contains `merged = 1`.")
    if "merged_at IS NOT NULL" not in nl2sql_prompt_text:
        failures.append("NL2SQL prompt missing `merged_at IS NOT NULL` guidance.")

    rag_prompt_text = RAG_PROMPT.read_text(encoding="utf-8")
    if "merged = 1" in rag_prompt_text:
        failures.append("RAG prompt still contains `merged = 1`.")
    if "merged_at" not in rag_prompt_text:
        failures.append("RAG prompt missing `merged_at` reference.")

    nl2sql_agent_def = NL2SQL_AGENT_DEF.read_text(encoding="utf-8")
    if "merged PRs use merged = 1" in nl2sql_agent_def:
        failures.append("Agent tool description still advertises `merged = 1`.")

    assert not failures, "Post-migration code upgrade gate failed:\n- " + "\n- ".join(failures)
