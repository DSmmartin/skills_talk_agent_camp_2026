import hashlib
import math
import re

import chromadb
from agents import function_tool
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from agentic_system.config import settings

# Must match DEFAULT_DIMENSIONS in db/vectordb/init/seed_vectors.py
_EMBEDDING_DIMENSIONS = 64


def _embed(text: str) -> list[float]:
    """Deterministic hash embedding — identical to the function used at seed time."""
    words = re.findall(r"[a-z0-9_]+", text.lower()) or ["empty"]
    tokens = list(words) + [f"{a}|{b}" for a, b in zip(words, words[1:])]

    vector = [0.0] * _EMBEDDING_DIMENSIONS
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        bucket = int.from_bytes(digest[:4], "big") % _EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weight = 1.0 + (digest[5] / 255.0)
        vector[bucket] += sign * weight

    magnitude = math.sqrt(sum(v * v for v in vector))
    return [v / magnitude for v in vector] if magnitude else vector


def _get_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def vector_search_core(query: str) -> str:
    """Search the vector database for schema context and SQL examples relevant to the query.

    Core logic — callable directly in scripts and tests without an agent context.

    Args:
        query: The natural language question or keyword to search for.

    Returns:
        Relevant schema field descriptions and example SQL snippets as a formatted string.
    """
    logger.info("vector_search start")
    logger.debug("vector_search query: {!r}", query)
    try:
        client = _get_client()
    except Exception as exc:
        logger.error(
            "ChromaDB connection failed ({}:{}): {}",
            settings.chroma_host,
            settings.chroma_port,
            exc,
        )
        return (
            f"ERROR: Could not connect to ChromaDB at "
            f"{settings.chroma_host}:{settings.chroma_port}. "
            f"Schema context is unavailable. Reason: {exc}"
        )

    chunks: list[str] = []

    for collection_name in ("schema_docs", "qa_examples"):
        try:
            collection = client.get_collection(collection_name)
            results = collection.query(query_embeddings=[_embed(query)], n_results=3)
            docs = results.get("documents", [[]])[0]
            if docs:
                chunks.extend(docs)
        except Exception as exc:
            logger.warning(
                "ChromaDB collection '{}' query failed: {}", collection_name, exc
            )

    if not chunks:
        logger.warning("vector_search returned no chunks for query: {!r}", query)
        return "No relevant context found in the vector database."

    logger.info("vector_search returned {} chunks", len(chunks))
    return "\n\n---\n\n".join(chunks)


@function_tool
def vector_search(query: str) -> str:
    """Search the vector database for schema context and SQL examples relevant to the query.

    Args:
        query: The natural language question or keyword to search for.

    Returns:
        Relevant schema field descriptions and example SQL snippets as a formatted string.
    """
    return vector_search_core(query)
