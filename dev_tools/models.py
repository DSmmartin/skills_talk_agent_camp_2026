"""
dev_tools/models.py

Shared dataclasses for the dev_tools package.
SchemaSyncReport is the canonical output of schema_sync.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SchemaSyncReport:
    """
    Complete change log produced by schema_sync.py.

    Attributes:
        table           — ClickHouse table that was synced
        dry_run         — True if no files/DBs were actually modified
        timestamp       — When the sync ran (UTC)
        live_schema     — {column: type} snapshot from ClickHouse at sync time
        yaml_changes    — List of YamlChange str-representations
        chroma_changes  — List of ChromaChange str-representations
        prompt_changes  — List of PromptChange str-representations
        rollback_state  — Snapshot saved for --rollback (None if not saved)
        errors          — Any non-fatal errors encountered
    """
    table: str
    dry_run: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    live_schema: dict[str, str] = field(default_factory=dict)
    yaml_changes: list[str] = field(default_factory=list)
    chroma_changes: list[str] = field(default_factory=list)
    prompt_changes: list[str] = field(default_factory=list)
    rollback_state: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)

    # ── Derived properties ─────────────────────────────────────────────────

    @property
    def total_changes(self) -> int:
        return len(self.yaml_changes) + len(self.chroma_changes) + len(self.prompt_changes)

    @property
    def layers_touched(self) -> list[str]:
        touched = []
        if self.yaml_changes:
            touched.append("YAML contract")
        if self.chroma_changes:
            touched.append("ChromaDB chunks")
        if self.prompt_changes:
            touched.append("Agent prompts")
        return touched

    # ── Display ────────────────────────────────────────────────────────────

    def print(self) -> None:
        tag = "[DRY RUN] " if self.dry_run else ""
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

        print(f"\n{'═' * 60}")
        print(f"  {tag}Schema Sync Report — {self.table}")
        print(f"  {ts}")
        print(f"{'═' * 60}")

        if self.yaml_changes:
            print(f"\n  YAML contract  ({len(self.yaml_changes)} change(s))")
            for c in self.yaml_changes:
                print(f"    • {c}")

        if self.chroma_changes:
            print(f"\n  ChromaDB chunks  ({len(self.chroma_changes)} chunk(s) patched)")
            for c in self.chroma_changes:
                print(f"    • {c}")

        if self.prompt_changes:
            print(f"\n  Agent prompts  ({len(self.prompt_changes)} file(s) patched)")
            for c in self.prompt_changes:
                print(f"    • {c}")

        if not self.total_changes:
            print("\n  No changes — all layers already match the live schema.")
        else:
            layers = ", ".join(self.layers_touched)
            print(f"\n  Total: {self.total_changes} change(s) across {layers}.")
            if self.dry_run:
                print("  Run without --dry-run to apply.")

        if self.errors:
            print(f"\n  ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"    ✗ {e}")

        print(f"{'═' * 60}\n")

    def to_dict(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "dry_run": self.dry_run,
            "timestamp": self.timestamp.isoformat(),
            "live_schema": self.live_schema,
            "yaml_changes": self.yaml_changes,
            "chroma_changes": self.chroma_changes,
            "prompt_changes": self.prompt_changes,
            "rollback_state": self.rollback_state,
            "errors": self.errors,
        }
