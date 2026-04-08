#!/usr/bin/env python3
"""
dev_tools/scripts/clickhouse_introspect.py

Introspects the live ClickHouse schema for a given table.
Returns a dict {column_name: type_string} in position order.

Used by schema_sync.py as Step 1: discover what the DB actually has.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentic_system.config import settings


def introspect(table: str = "github_events") -> dict[str, str]:
    """Return {column_name: type} for *table* from the live ClickHouse instance."""
    import clickhouse_connect

    client = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        user=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )
    result = client.query(
        f"SELECT name, type FROM system.columns "
        f"WHERE table = '{table}' ORDER BY position"
    )
    if not result.result_rows:
        raise ValueError(f"Table '{table}' not found in ClickHouse")
    return {row[0]: row[1] for row in result.result_rows}


def detect_drift(
    live: dict[str, str],
    contract: dict[str, str],
) -> tuple[list[str], list[str], list[tuple[str, str, str]]]:
    """
    Diff live schema vs YAML contract.

    Returns:
        added   — columns in live DB but not in contract
        removed — columns in contract but not in live DB
        changed — columns in both with different types: [(name, contract_type, live_type)]
    """
    live_names = set(live)
    contract_names = set(contract)

    added = sorted(live_names - contract_names)
    removed = sorted(contract_names - live_names)
    changed = sorted(
        (name, contract[name], live[name])
        for name in contract_names & live_names
        if contract[name] != live[name]
    )
    return added, removed, changed


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Introspect live ClickHouse schema and show column types"
    )
    parser.add_argument("--table", default="github_events", help="Table to introspect")
    args = parser.parse_args()

    print(f"==> ClickHouse Schema: {args.table}")
    print(f"    {settings.clickhouse_host}:{settings.clickhouse_port}/{settings.clickhouse_database}")
    print()

    try:
        cols = introspect(args.table)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    for name, typ in cols.items():
        print(f"  {name:25s}  {typ}")

    print(f"\n  {len(cols)} column(s) total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
