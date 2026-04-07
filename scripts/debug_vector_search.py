"""
scripts/debug_vector_search.py

Developer tool: run the ChromaDB vector search tool core logic directly without an agent context.

Usage:
    python scripts/debug_vector_search.py
    python scripts/debug_vector_search.py "ghost contributors merged PRs"
"""

import sys
from pathlib import Path

# Make the project root importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentic_system.agents_core.rag.tools.vector_search import vector_search_core
from agentic_system.config import settings

DEFAULT_QUERY = "*"


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY

    print(f"ChromaDB  {settings.chroma_host}:{settings.chroma_port}")
    print(f"Query: {query!r}\n")

    result = vector_search_core(query)

    if result.startswith("ERROR:"):
        print(result)
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
