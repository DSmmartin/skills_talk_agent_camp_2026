#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


ROOT_DIR = Path(__file__).resolve().parents[3]
VECTORDB_DIR = ROOT_DIR / "db" / "vectordb"
SCHEMA_DOCS_DIR = VECTORDB_DIR / "collections" / "schema_docs"
QA_EXAMPLES_DIR = VECTORDB_DIR / "collections" / "qa_examples"
DEFAULT_BASE_URL = os.environ.get("CHROMA_URL", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_TENANT = os.environ.get("CHROMA_TENANT", "default_tenant")
DEFAULT_DATABASE = os.environ.get("CHROMA_DATABASE", "default_database")
DEFAULT_DIMENSIONS = int(os.environ.get("VECTOR_DIMENSIONS", "64"))
DEFAULT_SMOKE_QUERY = (
    "Show me repositories where users opened PRs but never got one merged"
)


SEED_LAYOUT: Tuple[Tuple[str, str, Path], ...] = (
    ("schema_docs", "schema_doc", SCHEMA_DOCS_DIR / "pr_fields.txt"),
    ("qa_examples", "qa_example", QA_EXAMPLES_DIR / "ghost_contribs.txt"),
    ("qa_examples", "qa_example", QA_EXAMPLES_DIR / "unmerged_prs.txt"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed ChromaDB with schema docs and Q&A examples."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for ChromaDB.")
    parser.add_argument("--tenant", default=DEFAULT_TENANT, help="Chroma tenant name.")
    parser.add_argument("--database", default=DEFAULT_DATABASE, help="Chroma database name.")
    parser.add_argument(
        "--dimensions",
        type=int,
        default=DEFAULT_DIMENSIONS,
        help="Deterministic embedding dimension.",
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_SMOKE_QUERY,
        help="Smoke-test query to run after seeding.",
    )
    return parser.parse_args()


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9_]+", text.lower())
    if not words:
        return ["empty"]

    features = list(words)
    features.extend(f"{left}|{right}" for left, right in zip(words, words[1:]))
    return features


def deterministic_embedding(text: str, dimensions: int) -> List[float]:
    if dimensions <= 0:
        raise ValueError("dimensions must be greater than zero")

    vector = [0.0] * dimensions
    for token in tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weight = 1.0 + (digest[5] / 255.0)
        vector[bucket] += sign * weight

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector

    return [value / magnitude for value in vector]


def request_json(
    method: str,
    url: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Union[Dict[str, Any], List[Any], int]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: {exc.code} {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc

    if not body:
        return {}

    return json.loads(body)


def collection_base_url(base_url: str, tenant: str, database: str) -> str:
    return f"{base_url}/api/v2/tenants/{tenant}/databases/{database}/collections"


def create_or_get_collection(
    base_url: str,
    tenant: str,
    database: str,
    name: str,
    metadata: Dict[str, object],
) -> Dict:
    payload = {
        "name": name,
        "get_or_create": True,
        "metadata": metadata,
    }
    return request_json("POST", collection_base_url(base_url, tenant, database), payload)


def upsert_records(
    base_url: str,
    tenant: str,
    database: str,
    collection_id: str,
    records: List[Dict[str, object]],
    dimensions: int,
) -> Dict:
    payload = {
        "ids": [record["id"] for record in records],
        "documents": [record["document"] for record in records],
        "metadatas": [record["metadata"] for record in records],
        "embeddings": [
            deterministic_embedding(str(record["document"]), dimensions) for record in records
        ],
    }
    url = (
        f"{collection_base_url(base_url, tenant, database)}/{collection_id}/upsert"
    )
    return request_json("POST", url, payload)


def collection_count(
    base_url: str,
    tenant: str,
    database: str,
    collection_id: str,
) -> int:
    url = f"{collection_base_url(base_url, tenant, database)}/{collection_id}/count"
    result = request_json("GET", url)
    return int(result)


def query_collection(
    base_url: str,
    tenant: str,
    database: str,
    collection_id: str,
    query_text: str,
    dimensions: int,
    n_results: int = 2,
) -> Dict:
    payload = {
        "query_embeddings": [deterministic_embedding(query_text, dimensions)],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    url = f"{collection_base_url(base_url, tenant, database)}/{collection_id}/query"
    return request_json("POST", url, payload)


def load_seed_records() -> Dict[str, List[Dict[str, object]]]:
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for collection_name, doc_type, path in SEED_LAYOUT:
        text = path.read_text(encoding="utf-8").strip()
        record = {
            "id": f"{collection_name}:{path.stem}",
            "document": text,
            "metadata": {
                "source_file": str(path.relative_to(ROOT_DIR)),
                "doc_type": doc_type,
                "topic": path.stem,
                "migration_sensitive": True,
                "schema_state": "pre_migration",
            },
        }
        grouped.setdefault(collection_name, []).append(record)
    return grouped


def seed(args: argparse.Namespace) -> int:
    grouped_records = load_seed_records()

    print(f"Seeding ChromaDB at {args.base_url}")
    print(f"Tenant/database: {args.tenant}/{args.database}")
    print(f"Embedding dimensions: {args.dimensions}")

    collection_ids: Dict[str, str] = {}
    for collection_name, records in grouped_records.items():
        collection = create_or_get_collection(
            args.base_url,
            args.tenant,
            args.database,
            collection_name,
            {
                "seeded_by": "db/vectordb/init/seed_vectors.py",
                "schema_state": "pre_migration",
            },
        )
        collection_id = collection["id"]
        collection_ids[collection_name] = collection_id
        upsert_records(
            args.base_url,
            args.tenant,
            args.database,
            collection_id,
            records,
            args.dimensions,
        )
        count = collection_count(
            args.base_url,
            args.tenant,
            args.database,
            collection_id,
        )
        print(
            f"Seeded collection {collection_name} ({collection_id}) with {len(records)} seed docs; "
            f"collection count is now {count}"
        )

    query_result = query_collection(
        args.base_url,
        args.tenant,
        args.database,
        collection_ids["qa_examples"],
        args.query,
        args.dimensions,
        n_results=2,
    )
    top_ids = query_result.get("ids", [[]])[0]
    print(f"Smoke query: {args.query}")
    print(f"Top QA matches: {', '.join(top_ids)}")

    return 0


def main() -> int:
    try:
        return seed(parse_args())
    except Exception as exc:
        print(f"seed_vectors.py failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
