#!/usr/bin/env python3
"""
dev_tools/scripts/yaml_patch.py

Patches agentic_system/schema/<table>.yaml to match the live ClickHouse schema.

Specifically handles the schema migration:
  - Removes the `merged` column entry (or updates its description)
  - Adds/updates the `merged_at` column entry
  - Updates the `schema_state` metadata

Returns a list of ChangeRecord strings describing every modification made.

Used by schema_sync.py as Step 2: keep the YAML contract in sync with reality.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "agentic_system" / "schema"

# Column descriptions for known post-migration fields
_POST_MIGRATION_DESCRIPTIONS: dict[str, str] = {
    "merged_at": (
        "Post-migration field. Timestamp when the pull request was merged, "
        "or NULL if not merged. Replaces the pre-migration merged UInt8 flag. "
        "Use merged_at IS NOT NULL to filter merged PRs and "
        "merged_at IS NULL for unmerged."
    ),
    "merged": (
        "Legacy pre-migration field. Zeroed out after migration — always 0. "
        "Do NOT use merged = 1 after migration; use merged_at IS NOT NULL instead."
    ),
}


@dataclass
class YamlChange:
    action: str   # "added", "updated", "removed", "type_changed"
    column: str
    detail: str = ""

    def __str__(self) -> str:
        return f"yaml:{self.action}:{self.column}" + (f" ({self.detail})" if self.detail else "")


def load_yaml(table: str) -> dict[str, Any]:
    import yaml

    path = SCHEMA_DIR / f"{table}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Schema contract not found: {path}")
    with path.open() as f:
        return yaml.safe_load(f)


def save_yaml(table: str, doc: dict[str, Any]) -> None:
    import yaml

    path = SCHEMA_DIR / f"{table}.yaml"
    with path.open("w") as f:
        yaml.dump(doc, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def patch(
    table: str,
    live_cols: dict[str, str],
    dry_run: bool = False,
) -> list[YamlChange]:
    """
    Update the YAML contract so every live column is represented correctly.

    Returns the list of changes made (or that would be made in dry_run mode).
    """
    doc = load_yaml(table)
    columns: list[dict] = doc.get("columns", [])
    changes: list[YamlChange] = []

    # Index existing YAML columns by name for fast lookup
    yaml_by_name: dict[str, dict] = {col["name"]: col for col in columns}

    for col_name, live_type in live_cols.items():
        if col_name in yaml_by_name:
            existing = yaml_by_name[col_name]
            # Update type if it changed
            if existing.get("type") != live_type:
                changes.append(YamlChange(
                    "type_changed", col_name,
                    f"{existing.get('type')} → {live_type}",
                ))
                if not dry_run:
                    existing["type"] = live_type
            # Update description for known migration-sensitive columns
            if col_name in _POST_MIGRATION_DESCRIPTIONS:
                new_desc = _POST_MIGRATION_DESCRIPTIONS[col_name]
                if existing.get("description", "").strip() != new_desc.strip():
                    changes.append(YamlChange(
                        "updated", col_name, "description refreshed for post-migration state"
                    ))
                    if not dry_run:
                        existing["description"] = new_desc
        else:
            # New column — add it to the YAML
            new_entry: dict[str, Any] = {"name": col_name, "type": live_type}
            if col_name in _POST_MIGRATION_DESCRIPTIONS:
                new_entry["description"] = _POST_MIGRATION_DESCRIPTIONS[col_name]
            else:
                new_entry["description"] = f"{col_name} column (added by schema-sync)"
            changes.append(YamlChange("added", col_name, live_type))
            if not dry_run:
                columns.append(new_entry)

    # Mark schema_state if the doc has it
    if not dry_run and changes:
        doc["schema_state"] = "post_migration_synced"

    if not dry_run and changes:
        save_yaml(table, doc)

    return changes


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> int:
    import argparse
    from dev_tools.scripts.clickhouse_introspect import introspect

    parser = argparse.ArgumentParser(
        description="Patch the YAML schema contract to match live ClickHouse"
    )
    parser.add_argument("--table", default="github_events")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tag = "[DRY RUN] " if args.dry_run else ""
    print(f"{tag}==> YAML Patch: {args.table}")

    live = introspect(args.table)
    changes = patch(args.table, live, dry_run=args.dry_run)

    if not changes:
        print("  No changes — YAML already matches live schema.")
        return 0

    for c in changes:
        print(f"  {c}")

    print(f"\n  {len(changes)} change(s) {'would be ' if args.dry_run else ''}applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
