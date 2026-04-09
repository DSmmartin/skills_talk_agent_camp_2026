#!/usr/bin/env python3
"""
scripts/migrate_schema.py

Schema migration helper: rename merged (UInt8) → merged_at (Nullable(DateTime)) in ClickHouse.
Also marks migration-sensitive ChromaDB chunks as stale.
Content in ChromaDB is intentionally left wrong — the agent will return silent
wrong answers until schema_sync repairs the affected layers.

Usage:
    python scripts/migrate_schema.py
    python scripts/migrate_schema.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentic_system.config import settings

CHROMA_BASE_URL = f"http://{settings.chroma_host}:{settings.chroma_port}"
CHROMA_TENANT = "default_tenant"
CHROMA_DATABASE = "default_database"


# ── ChromaDB HTTP helpers ──────────────────────────────────────────────────────

def _chroma_request(method: str, url: str, payload: dict | None = None) -> object:
    data, headers = None, {}
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {url} → {exc.code}: {exc.read().decode()}") from exc


def _col_url(collection_id: str) -> str:
    return (
        f"{CHROMA_BASE_URL}/api/v2/tenants/{CHROMA_TENANT}"
        f"/databases/{CHROMA_DATABASE}/collections/{collection_id}"
    )


def list_collections() -> list[dict]:
    url = (
        f"{CHROMA_BASE_URL}/api/v2/tenants/{CHROMA_TENANT}"
        f"/databases/{CHROMA_DATABASE}/collections"
    )
    return _chroma_request("GET", url)  # type: ignore[return-value]


def get_all_items(collection_id: str) -> dict:
    return _chroma_request("POST", f"{_col_url(collection_id)}/get", {"include": ["metadatas"]})  # type: ignore[return-value]


def update_metadata(collection_id: str, ids: list[str], metadatas: list[dict]) -> None:
    _chroma_request("POST", f"{_col_url(collection_id)}/update", {"ids": ids, "metadatas": metadatas})


# ── ClickHouse helpers ─────────────────────────────────────────────────────────

def _ch_client():
    import clickhouse_connect
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        user=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


def current_columns(client) -> dict[str, str]:
    result = client.query(
        "SELECT name, type FROM system.columns WHERE table = 'github_events' ORDER BY position"
    )
    return {row[0]: row[1] for row in result.result_rows}


def run_ch(client, sql: str, dry_run: bool, label: str) -> None:
    print(f"  {label}")
    if dry_run:
        print(f"    [dry-run] {sql}")
        return
    client.command(sql)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 schema migration: merged → merged_at")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, touch nothing")
    args = parser.parse_args()
    dry_run: bool = args.dry_run
    tag = "[DRY RUN] " if dry_run else ""

    print(f"{tag}==> Phase 2 Schema Migration")
    print(f"    ClickHouse  {settings.clickhouse_host}:{settings.clickhouse_port}/{settings.clickhouse_database}")
    print(f"    ChromaDB    {CHROMA_BASE_URL}")
    print()

    # ── ClickHouse ──────────────────────────────────────────────────────────
    print("── ClickHouse ──────────────────────────────────────────────────")
    client = _ch_client()
    cols = current_columns(client)

    if "merged_at" in cols:
        print("  ERROR: merged_at already exists — already migrated.")
        print("  Run 'make rollback' first to reset to pre-migration state.")
        return 1
    if "merged" not in cols:
        print("  ERROR: merged column not found — unexpected schema state.")
        return 1

    run_ch(
        client,
        "ALTER TABLE github_events ADD COLUMN merged_at Nullable(DateTime) DEFAULT NULL",
        dry_run,
        "1/3  ADD COLUMN merged_at Nullable(DateTime) DEFAULT NULL",
    )
    run_ch(
        client,
        (
            "ALTER TABLE github_events "
            "UPDATE merged_at = if(merged = 1, created_at, NULL) WHERE 1 "
            "SETTINGS mutations_sync = 1"
        ),
        dry_run,
        "2/3  UPDATE merged_at = if(merged=1, created_at, NULL)  [waiting for mutation…]",
    )
    # Zero out merged instead of dropping it.
    # Dropping would cause ClickHouse to throw UNKNOWN_IDENTIFIER when old SQL runs.
    # Zeroing makes merged = 1 execute silently and return 0 rows — the intended Phase 2 effect.
    run_ch(
        client,
        (
            "ALTER TABLE github_events "
            "UPDATE merged = 0 WHERE 1 "
            "SETTINGS mutations_sync = 1"
        ),
        dry_run,
        "3/3  UPDATE merged = 0  (zero out — makes merged=1 silently return 0 rows)  [waiting…]",
    )

    if not dry_run:
        after = list(current_columns(client).keys())
        r = client.query("SELECT countIf(merged = 1) FROM github_events WHERE event_type = 'PullRequestEvent'")
        merged_count = r.result_rows[0][0]
        print(f"  Columns now: {after}")
        print(f"  Rows where merged=1: {merged_count}  (should be 0)")
    print()

    # ── ChromaDB: mark sensitive chunks stale ──────────────────────────────
    print("── ChromaDB ────────────────────────────────────────────────────")
    collections = list_collections()
    total_stale = 0

    for col in collections:
        col_id: str = col["id"]
        col_name: str = col["name"]
        items = get_all_items(col_id)
        ids: list[str] = items.get("ids", [])
        metadatas: list[dict] = items.get("metadatas", []) or []

        sensitive: list[tuple[str, dict]] = [
            (ids[i], metadatas[i])
            for i in range(len(ids))
            if (metadatas[i] or {}).get("migration_sensitive")
        ]
        if not sensitive:
            continue

        stale_ids = [s[0] for s in sensitive]
        stale_metas = [
            {**s[1], "stale": True, "schema_state": "post_migration_stale"}
            for s in sensitive
        ]

        print(f"  {col_name}: {len(stale_ids)} chunk(s) → stale")
        for sid in stale_ids:
            print(f"    {sid}")

        if not dry_run:
            update_metadata(col_id, stale_ids, stale_metas)
        else:
            print(f"    [dry-run] would update {stale_ids}")

        total_stale += len(stale_ids)

    print(f"  {total_stale} chunk(s) marked stale  (content intentionally left wrong)")
    print()

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"{tag}Migration complete.")
    if not dry_run:
        print("  Phase 2 is now active:")
        print("    • ClickHouse: merged_at Nullable(DateTime)  (merged column gone)")
        print("    • ChromaDB:   stale chunks with old field names still in RAG")
        print("    • Agent will return 0 rows silently — no exception thrown.")
        print()
        print("  To restore:  make rollback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
