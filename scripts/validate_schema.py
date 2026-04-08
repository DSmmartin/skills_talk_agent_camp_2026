#!/usr/bin/env python3
"""
scripts/validate_schema.py

Diff the live ClickHouse schema for github_events against the YAML contract
at agentic_system/schema/github_events.yaml.

Useful after a migration to understand what has drifted before running schema-sync.

Usage:
    python scripts/validate_schema.py
    python scripts/validate_schema.py --table github_events
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentic_system.config import settings

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "agentic_system" / "schema"


def load_yaml_contract(table: str) -> dict[str, str]:
    """Return {column_name: type} from the YAML schema file."""
    schema_file = SCHEMA_DIR / f"{table}.yaml"
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema contract not found: {schema_file}")

    import yaml  # available transitively via chromadb/mlflow deps
    with schema_file.open() as f:
        doc = yaml.safe_load(f)

    return {col["name"]: col["type"] for col in doc.get("columns", [])}


def load_live_schema(table: str) -> dict[str, str]:
    """Return {column_name: type} from ClickHouse system.columns."""
    import clickhouse_connect
    client = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        user=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )
    result = client.query(
        f"SELECT name, type FROM system.columns WHERE table = '{table}' ORDER BY position"
    )
    if not result.result_rows:
        raise ValueError(f"Table '{table}' not found in ClickHouse")
    return {row[0]: row[1] for row in result.result_rows}


def diff_schemas(
    yaml_cols: dict[str, str],
    live_cols: dict[str, str],
) -> tuple[list[str], list[str], list[tuple[str, str, str]]]:
    """
    Returns:
        added   — in live DB but not in YAML contract
        removed — in YAML contract but not in live DB
        changed — in both but different types: [(name, yaml_type, live_type)]
    """
    yaml_names = set(yaml_cols)
    live_names = set(live_cols)

    added = sorted(live_names - yaml_names)
    removed = sorted(yaml_names - live_names)
    changed = sorted(
        (name, yaml_cols[name], live_cols[name])
        for name in yaml_names & live_names
        if yaml_cols[name] != live_cols[name]
    )
    return added, removed, changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diff live ClickHouse schema against YAML contract"
    )
    parser.add_argument("--table", default="github_events", help="Table to validate")
    args = parser.parse_args()
    table: str = args.table

    print(f"==> Schema Validation: {table}")
    print(f"    ClickHouse  {settings.clickhouse_host}:{settings.clickhouse_port}/{settings.clickhouse_database}")
    print(f"    Contract    agentic_system/schema/{table}.yaml")
    print()

    try:
        yaml_cols = load_yaml_contract(table)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    try:
        live_cols = load_live_schema(table)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    added, removed, changed = diff_schemas(yaml_cols, live_cols)

    # ── YAML contract ──────────────────────────────────────────────────────
    print("── YAML Contract ───────────────────────────────────────────────")
    for name, typ in yaml_cols.items():
        marker = ""
        if name in {r for r in removed}:
            marker = "  ← MISSING IN DB"
        elif name in {c[0] for c in changed}:
            live_type = live_cols.get(name, "?")
            marker = f"  ← TYPE MISMATCH (live: {live_type})"
        print(f"  {name:20s}  {typ}{marker}")
    print()

    # ── Live schema ────────────────────────────────────────────────────────
    print("── Live ClickHouse Schema ──────────────────────────────────────")
    for name, typ in live_cols.items():
        marker = ""
        if name in added:
            marker = "  ← NOT IN CONTRACT"
        elif name in {c[0] for c in changed}:
            yaml_type = yaml_cols.get(name, "?")
            marker = f"  ← TYPE MISMATCH (contract: {yaml_type})"
        print(f"  {name:20s}  {typ}{marker}")
    print()

    # ── Drift report ───────────────────────────────────────────────────────
    print("── Drift Report ────────────────────────────────────────────────")
    if not added and not removed and not changed:
        print("  No drift — live schema matches YAML contract exactly.")
        return 0

    if removed:
        print("  REMOVED (in contract, gone from DB):")
        for name in removed:
            print(f"    - {name:20s}  {yaml_cols[name]}")

    if added:
        print("  ADDED (in DB, not in contract):")
        for name in added:
            print(f"    + {name:20s}  {live_cols[name]}")

    if changed:
        print("  TYPE CHANGED:")
        for name, yaml_type, live_type in changed:
            print(f"    ~ {name:20s}  {yaml_type}  →  {live_type}")

    print()
    total = len(added) + len(removed) + len(changed)
    print(f"  {total} drift(s) detected.")
    print("  Run 'python dev_tools/schema_sync.py --table github_events' to patch all layers.")
    return 1  # non-zero exit = drift found


if __name__ == "__main__":
    raise SystemExit(main())
