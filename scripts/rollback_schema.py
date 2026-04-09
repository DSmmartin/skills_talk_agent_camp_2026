#!/usr/bin/env python3
"""
scripts/rollback_schema.py

Reverses the Phase 2 migration: merged_at (Nullable(DateTime)) → merged (UInt8).
Restores ChromaDB chunk metadata to pre_migration state.

Usage:
    python scripts/rollback_schema.py
    python scripts/rollback_schema.py --dry-run
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
    parser = argparse.ArgumentParser(description="Rollback Phase 2 migration: merged_at → merged")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, touch nothing")
    args = parser.parse_args()
    dry_run: bool = args.dry_run
    tag = "[DRY RUN] " if dry_run else ""

    print(f"{tag}==> Phase 2 Schema Rollback")
    print(f"    ClickHouse  {settings.clickhouse_host}:{settings.clickhouse_port}/{settings.clickhouse_database}")
    print(f"    ChromaDB    {CHROMA_BASE_URL}")
    print()

    # ── ClickHouse ──────────────────────────────────────────────────────────
    print("── ClickHouse ──────────────────────────────────────────────────")
    client = _ch_client()
    cols = current_columns(client)

    if "merged" in cols and "merged_at" not in cols:
        print("  Already at pre-migration state — nothing to roll back.")
        return 0
    if "merged_at" not in cols or "merged" not in cols:
        print("  ERROR: unexpected schema state — expected both merged and merged_at to exist.")
        print(f"  Current columns: {list(cols.keys())}")
        return 1

    # Restore merged values from merged_at (re-derive the 0/1 flag)
    run_ch(
        client,
        (
            "ALTER TABLE github_events "
            "UPDATE merged = if(isNotNull(merged_at), toUInt8(1), toUInt8(0)) WHERE 1 "
            "SETTINGS mutations_sync = 1"
        ),
        dry_run,
        "1/2  UPDATE merged = if(isNotNull(merged_at), 1, 0)  [waiting for mutation…]",
    )
    run_ch(
        client,
        "ALTER TABLE github_events DROP COLUMN merged_at",
        dry_run,
        "2/2  DROP COLUMN merged_at",
    )

    if not dry_run:
        after = list(current_columns(client).keys())
        r = client.query("SELECT countIf(merged = 1) FROM github_events WHERE event_type = 'PullRequestEvent'")
        merged_count = r.result_rows[0][0]
        print(f"  Columns now: {after}")
        print(f"  Rows where merged=1: {merged_count}  (should be ~1.6M)")
    print()

    # ── ChromaDB: restore pre_migration metadata ───────────────────────────
    print("── ChromaDB ────────────────────────────────────────────────────")
    collections = list_collections()
    restored = 0

    for col in collections:
        col_id: str = col["id"]
        col_name: str = col["name"]
        items = get_all_items(col_id)
        ids: list[str] = items.get("ids", [])
        metadatas: list[dict] = items.get("metadatas", []) or []

        stale: list[tuple[str, dict]] = [
            (ids[i], metadatas[i])
            for i in range(len(ids))
            if (metadatas[i] or {}).get("stale")
        ]
        if not stale:
            continue

        restore_ids = [s[0] for s in stale]
        restore_metas = []
        for _, meta in stale:
            cleaned = {k: v for k, v in meta.items() if k != "stale"}
            cleaned["schema_state"] = "pre_migration"
            restore_metas.append(cleaned)

        print(f"  {col_name}: {len(restore_ids)} chunk(s) → pre_migration")
        for rid in restore_ids:
            print(f"    {rid}")

        if not dry_run:
            update_metadata(col_id, restore_ids, restore_metas)
        else:
            print(f"    [dry-run] would restore {restore_ids}")

        restored += len(restore_ids)

    print(f"  {restored} chunk(s) restored to pre_migration state")
    print()

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"{tag}Rollback complete.")
    if not dry_run:
        print("  Pre-migration state restored:")
        print("    • ClickHouse: merged UInt8 values restored  (merged_at column gone)")
        print("    • ChromaDB:   chunks back to schema_state=pre_migration")
        print("    • Agent will return correct rows again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
