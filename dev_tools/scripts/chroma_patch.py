#!/usr/bin/env python3
"""
dev_tools/scripts/chroma_patch.py

Finds stale ChromaDB chunks (metadata.stale == True) and patches their content
to reflect the post-migration schema (merged_at DateTime NULL instead of merged UInt8).

Steps per chunk:
  1. Fetch the stale document text
  2. Apply text replacements: merged UInt8 → merged_at, SQL predicates, etc.
  3. Re-embed with the same deterministic hash embedding used at seed time
  4. Upsert back into the collection with schema_state=post_migration_synced

Returns a list of patched chunk IDs.

Used by schema_sync.py as Step 3.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentic_system.config import settings

CHROMA_BASE_URL = f"http://{settings.chroma_host}:{settings.chroma_port}"
CHROMA_TENANT = "default_tenant"
CHROMA_DATABASE = "default_database"
EMBEDDING_DIMENSIONS = 64

# Text replacement rules: each (pattern, replacement) pair is applied in order.
# Designed to transform pre-migration schema text → post-migration schema text.
_REPLACEMENTS: list[tuple[str, str]] = [
    # Field name in prose
    (r"\bmerged UInt8\b", "merged_at Nullable(DateTime)"),
    (r"\bmerged_at DateTime NULL\b", "merged_at Nullable(DateTime)"),
    # SQL predicates
    (r"\bmerged\s*=\s*1\b", "merged_at IS NOT NULL"),
    (r"\bmerged\s*=\s*0\b", "merged_at IS NULL"),
    # Descriptions referencing the old flag
    (
        r"1 means the pull request was merged and 0 means it was not merged",
        "non-NULL means the pull request was merged, NULL means it was not merged",
    ),
    (
        r"Use merged = 1 to identify merged pull requests",
        "Use merged_at IS NOT NULL to identify merged pull requests",
    ),
    (
        r"Use merged = 0 to identify pull requests that were closed without being merged",
        "Use merged_at IS NULL to identify pull requests that were closed without being merged",
    ),
    # State markers
    (r"State: pre-migration", "State: post-migration"),
    (r"pre-migration merge flag where", "post-migration timestamp,"),
    (r"schema_state.*pre_migration", "schema_state: post_migration_synced"),
]


@dataclass
class ChromaChange:
    chunk_id: str
    collection: str
    replacements_applied: int

    def __str__(self) -> str:
        return f"chroma:patched:{self.chunk_id} ({self.replacements_applied} replacement(s))"


# ── Embedding ──────────────────────────────────────────────────────────────────


def _embed(text: str) -> list[float]:
    words = re.findall(r"[a-z0-9_]+", text.lower()) or ["empty"]
    tokens = list(words) + [f"{a}|{b}" for a, b in zip(words, words[1:])]
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        bucket = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weight = 1.0 + (digest[5] / 255.0)
        vector[bucket] += sign * weight
    magnitude = math.sqrt(sum(v * v for v in vector))
    return [v / magnitude for v in vector] if magnitude else vector


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
        raise RuntimeError(
            f"{method} {url} → {exc.code}: {exc.read().decode()}"
        ) from exc


def _col_url(collection_id: str) -> str:
    return (
        f"{CHROMA_BASE_URL}/api/v2/tenants/{CHROMA_TENANT}"
        f"/databases/{CHROMA_DATABASE}/collections/{collection_id}"
    )


def _list_collections() -> list[dict]:
    url = (
        f"{CHROMA_BASE_URL}/api/v2/tenants/{CHROMA_TENANT}"
        f"/databases/{CHROMA_DATABASE}/collections"
    )
    return _chroma_request("GET", url)  # type: ignore[return-value]


def _get_all_items(collection_id: str) -> dict:
    return _chroma_request(  # type: ignore[return-value]
        "POST",
        f"{_col_url(collection_id)}/get",
        {"include": ["documents", "metadatas"]},
    )


def _upsert(
    collection_id: str, ids: list[str], documents: list[str], metadatas: list[dict]
) -> None:
    _chroma_request(
        "POST",
        f"{_col_url(collection_id)}/upsert",
        {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "embeddings": [_embed(doc) for doc in documents],
        },
    )


# ── Core patch logic ───────────────────────────────────────────────────────────


def _apply_text_replacements(text: str) -> tuple[str, int]:
    """Apply all _REPLACEMENTS to *text*. Returns (new_text, count_applied)."""
    count = 0
    for pattern, replacement in _REPLACEMENTS:
        new_text, n = re.subn(pattern, replacement, text)
        count += n
        text = new_text
    return text, count


def patch(dry_run: bool = False) -> list[ChromaChange]:
    """
    Find all stale chunks, patch their content, re-embed, and upsert.
    Returns list of ChromaChange records.
    """
    changes: list[ChromaChange] = []
    collections = _list_collections()

    for col in collections:
        col_id: str = col["id"]
        col_name: str = col["name"]
        items = _get_all_items(col_id)

        ids: list[str] = items.get("ids", [])
        documents: list[str] = items.get("documents", []) or []
        metadatas: list[dict] = items.get("metadatas", []) or []

        # Find stale chunks
        stale_indices = [
            i for i in range(len(ids)) if (metadatas[i] or {}).get("stale")
        ]
        if not stale_indices:
            continue

        patch_ids, patch_docs, patch_metas = [], [], []
        for i in stale_indices:
            doc = documents[i] if i < len(documents) else ""
            new_doc, n_replacements = _apply_text_replacements(doc)

            new_meta = {
                **metadatas[i],
                "stale": False,
                "schema_state": "post_migration_synced",
            }

            patch_ids.append(ids[i])
            patch_docs.append(new_doc)
            patch_metas.append(new_meta)
            changes.append(ChromaChange(ids[i], col_name, n_replacements))

        if not dry_run:
            _upsert(col_id, patch_ids, patch_docs, patch_metas)

    return changes


# ── CLI ────────────────────────────────────────────────────────────────────────


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Patch stale ChromaDB chunks to reflect the post-migration schema"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tag = "[DRY RUN] " if args.dry_run else ""
    print(f"{tag}==> ChromaDB Patch")
    print(f"    {CHROMA_BASE_URL}")
    print()

    try:
        changes = patch(dry_run=args.dry_run)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    if not changes:
        print("  No stale chunks found — nothing to patch.")
        return 0

    for c in changes:
        print(f"  {c}")

    action = "would be " if args.dry_run else ""
    print(f"\n  {len(changes)} chunk(s) {action}patched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
