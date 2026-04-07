"""
scripts/explore_vectordb.py

Quick exploratory dump of ChromaDB contents — no embeddings needed.
Shows every document stored in schema_docs and qa_examples so you
know what context the RAG agent has and what questions make sense.

Usage:
    uv run python scripts/explore_vectordb.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb
from chromadb.config import Settings as ChromaSettings

from agentic_system.config import settings

SEP = "─" * 72


def dump_collection(client: chromadb.HttpClient, name: str) -> None:
    try:
        col = client.get_collection(name)
    except Exception as exc:
        print(f"  [MISSING] {name}: {exc}\n")
        return

    data = col.get(include=["documents", "metadatas"])
    ids = data.get("ids", [])
    docs = data.get("documents", [])
    metas = data.get("metadatas", [])

    print(f"\n{'━'*72}")
    print(f"  COLLECTION: {name}  ({len(ids)} document(s))")
    print(f"{'━'*72}")

    for doc_id, doc, meta in zip(ids, docs, metas):
        print(f"\n  id       : {doc_id}")
        print(f"  metadata : {meta}")
        print(f"  {SEP}")
        # Indent each line of the document body
        for line in (doc or "").splitlines():
            print(f"  {line}")
        print()


def main() -> None:
    client = chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    print(f"ChromaDB  {settings.chroma_host}:{settings.chroma_port}")

    for col_name in ("schema_docs", "qa_examples"):
        dump_collection(client, col_name)

    print(f"\n{'━'*72}")
    print("  SUGGESTED QUESTIONS for the agent")
    print(f"{'━'*72}")
    print("""
  Schema-level (answered from schema_docs):
    • What fields are available in the github_events table?
    • What does the merged column represent?
    • How are timestamps stored in the dataset?

  Data-level (answered by running SQL via nl2sql):
    • How many PRs were merged in 2023?
    • Which repositories have the highest PR rejection rate?
    • Who are the top contributors by number of opened PRs?
    • Show me ghost contributors — users who opened PRs but never got one merged.
    • What is the monthly PR volume trend for the last 12 months?
    • Which repos have the longest average time-to-merge?
""")


if __name__ == "__main__":
    main()
