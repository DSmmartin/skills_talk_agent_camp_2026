---
id: INF-05
name: ChromaDB Seed for Schema Docs and Q&A Examples
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Seed ChromaDB with schema context and Q&A examples for retrieval workflows.
---

# INF-05 - ChromaDB Seed for Schema Docs and Q&A Examples

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: M
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L615)

## Objective

Seed ChromaDB with the initial schema documentation and Q&A examples that AgentRAG will retrieve during the pre-migration demo flow.

## Description

This task defines the first content layer for the vector database. Its purpose is to populate ChromaDB with the minimum set of documents required to support the Act 1 demo and the later Act 2 break/heal narrative: a schema reference chunk for `github_events` and example Q&A chunks that explicitly depend on the pre-migration `merged UInt8` field.

The task should include both the source documents stored in the repository and the script that embeds and loads them into ChromaDB. It should remain focused on vector seed content only, not compose wiring, not runtime agent logic, and not schema-sync patching behavior.

## Scope

- Create the ChromaDB seed script at `db/vectordb/init/seed_vectors.py`.
- Add the initial schema document under `db/vectordb/collections/schema_docs/`.
- Add the initial Q&A example documents under `db/vectordb/collections/qa_examples/`.
- Seed ChromaDB collections for schema docs and Q&A examples.
- Keep the content aligned with the pre-migration `merged UInt8` story in the backlog.
- Make the seeding flow explicit enough to be reused later by `make seed-vectors`.

## Out Of Scope

- Wiring the seed script into `docker-compose.yml` or `Makefile`.
- Implementing AgentRAG or retrieval logic in the application layer.
- Re-embedding migrated content after the schema changes.
- Creating YAML schema files for agents.
- Implementing MLflow logging or evaluation flows.
- Performing cross-platform cold-start validation.

## Deliverables

- A vector seed script at `db/vectordb/init/seed_vectors.py`.
- A schema documentation seed file at `db/vectordb/collections/schema_docs/pr_fields.txt`.
- Q&A example seed files at `db/vectordb/collections/qa_examples/ghost_contribs.txt` and `db/vectordb/collections/qa_examples/unmerged_prs.txt`.
- Seed logic that loads the initial documents into ChromaDB collections for `schema_docs` and `qa_examples`.
- A backlog task artifact at `backlog/INF-05.md` that records the task scope, outputs, and status.

## Acceptance Criteria

- `db/vectordb/init/seed_vectors.py` exists.
- The repository contains the initial schema doc and Q&A example files named in the product backlog.
- The seed flow populates ChromaDB collections for schema docs and Q&A examples.
- The seeded content reflects the pre-migration `merged UInt8` contract and the example SQL patterns `merged = 1` and `merged = 0`.
- The task does not absorb compose wiring, agent implementation, or schema-sync responsibilities.

## Dependencies

- `INF-04` completed so the ChromaDB container baseline already exists.
- Product decision to store schema docs and Q&A examples in ChromaDB for AgentRAG retrieval.
- Pre-migration ClickHouse schema from `INF-02` so the vector content matches the Act 1 database contract.

## Assumptions

- The initial demo only needs a small, high-signal seed set rather than a large corpus of documents.
- Two collections, `schema_docs` and `qa_examples`, are sufficient for the initial RAG baseline.
- The content should intentionally preserve the pre-migration `merged` field references so later migration tasks have something meaningful to invalidate.
- The local seed flow should be runnable against a live ChromaDB server over HTTP.

## Verification

Procedure used to verify the task against a live ChromaDB container:

1. Compile-check `db/vectordb/init/seed_vectors.py` with a workspace-local pycache path.
2. Run the seed script against the live ChromaDB container exposed on `http://127.0.0.1:8001`.
3. Confirm the script reports `schema_docs` count `1` and `qa_examples` count `2`.
4. Run an independent HTTP verification against ChromaDB to confirm the seeded collection counts.
5. Query the `qa_examples` collection with the Act 1 user question and confirm `qa_examples:ghost_contribs` is returned as the top match.

Commands used:

```bash
PYTHONPYCACHEPREFIX=.pycache python3 -m py_compile db/vectordb/init/seed_vectors.py
python3 db/vectordb/init/seed_vectors.py --base-url http://127.0.0.1:8001
python3 - <<'PY'
import importlib.util
import json
import urllib.request
from pathlib import Path

spec = importlib.util.spec_from_file_location('seed_vectors', Path('db/vectordb/init/seed_vectors.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = 'http://127.0.0.1:8001/api/v2/tenants/default_tenant/databases/default_database/collections'
with urllib.request.urlopen(base, timeout=10) as response:
    collections = json.load(response)

qa_id = None
for collection in collections:
    if collection['name'] == 'schema_docs':
        with urllib.request.urlopen(f"{base}/{collection['id']}/count", timeout=10) as response:
            print('schema_docs_count', json.load(response))
    if collection['name'] == 'qa_examples':
        qa_id = collection['id']
        with urllib.request.urlopen(f"{base}/{collection['id']}/count", timeout=10) as response:
            print('qa_examples_count', json.load(response))

payload = json.dumps({
    'query_embeddings': [module.deterministic_embedding('Show me repositories where users opened PRs but never got one merged', 64)],
    'n_results': 2,
    'include': ['documents', 'metadatas', 'distances'],
}).encode('utf-8')
request = urllib.request.Request(
    f"{base}/{qa_id}/query",
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(request, timeout=10) as response:
    result = json.load(response)
    print('qa_top_ids', result['ids'][0])
PY
```

Expected verification result:

- The seed script compiles cleanly.
- The live ChromaDB server accepts the seed data over HTTP.
- `schema_docs` contains `1` document.
- `qa_examples` contains `2` documents.
- The Act 1 user question retrieves `qa_examples:ghost_contribs` as the top QA example.

## Notes

- Created on 2026-04-07 as the next Epic 1 task after `INF-04`.
- Completed on 2026-04-07.
- Implemented `db/vectordb/init/seed_vectors.py` as a stdlib-only ChromaDB seed script using deterministic local embeddings.
- Added the initial migration-sensitive seed documents:
  `db/vectordb/collections/schema_docs/pr_fields.txt`,
  `db/vectordb/collections/qa_examples/ghost_contribs.txt`,
  and `db/vectordb/collections/qa_examples/unmerged_prs.txt`.
- Verified against the live ChromaDB container `skills-talk-chromadb-live` using host port `8001`.
