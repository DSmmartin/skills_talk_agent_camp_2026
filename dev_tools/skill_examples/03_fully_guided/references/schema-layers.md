# Schema Layers Reference

Detailed field mapping and patch instructions for each layer of the Ghost Contributors system.

---

## The schema migration

| Before | After | Impact |
|--------|-------|--------|
| `merged UInt8` — 1 = merged, 0 = not merged | `merged_at Nullable(DateTime)` — timestamp or NULL | All `merged = 1` predicates return 0 rows silently |
| `merged` still exists (zeroed to 0) | `merged_at` added with timestamps | `merged = 1` still executes but always 0 |

---

## Layer 1 — YAML contract

**File:** `agentic_system/schema/github_events.yaml`

Post-migration, the YAML should have:

```yaml
- name: merged
  type: UInt8
  description: >
    Legacy pre-migration field. Zeroed out after migration — always 0.
    Do NOT use merged = 1 after migration; use merged_at IS NOT NULL instead.

- name: merged_at
  type: Nullable(DateTime)
  description: >
    Post-migration field. Timestamp when the pull request was merged,
    or NULL if not merged. Replaces the pre-migration merged UInt8 flag.
    Use merged_at IS NOT NULL to filter merged PRs and
    merged_at IS NULL for unmerged.
```

---

## Layer 2 — NL2SQL system prompt

**File:** `agentic_system/agents_core/nl2sql/prompts/system.md`

Replacement list (apply in this order):

| Find | Replace |
|------|---------|
| `\| merged \| UInt8 \| ... \|` (table row) | `\| merged_at \| Nullable(DateTime) \| Post-migration. NULL = not merged; non-NULL = merged timestamp. \|` |
| `merged UInt8` | `merged_at Nullable(DateTime)` |
| `merged = 1` | `merged_at IS NOT NULL` |
| `merged = 0` | `merged_at IS NULL` |
| `` `merged = 1` `` | `` `merged_at IS NOT NULL` `` |
| `` `merged = 0` `` | `` `merged_at IS NULL` `` |
| `sum(merged)` | `countIf(isNotNull(merged_at))` |
| `Use \`merged = 1\` for merged PRs and \`merged = 0\` for unmerged (pre-migration).` | `Use \`merged_at IS NOT NULL\` for merged PRs and \`merged_at IS NULL\` for unmerged (post-migration).` |
| `**1** if the PR was merged, **0** if closed without merging.` | `**non-NULL** (timestamp) if the PR was merged, **NULL** if closed without merging.` |
| `(pre-migration)` | `(post-migration)` |

---

## Layer 3 — RAG system prompt

**File:** `agentic_system/agents_core/rag/prompts/system.md`

Same replacement list as Layer 2. The RAG prompt is shorter and typically only contains a few
references to `merged` in the table context section.

---

## Layer 4 — ChromaDB RAG chunks

**Collections:** `schema_docs`, `qa_examples`

**How to find stale chunks:**

```python
# GET items with metadata
POST /api/v2/tenants/default_tenant/databases/default_database/collections/{id}/get
{"include": ["documents", "metadatas"]}

# Stale chunks have: metadata.stale == True
```

**Text replacements** (same as prompts, plus):

| Find | Replace |
|------|---------|
| `merged UInt8` | `merged_at Nullable(DateTime)` |
| `merged = 1` | `merged_at IS NOT NULL` |
| `merged = 0` | `merged_at IS NULL` |
| `1 means the pull request was merged and 0 means it was not merged` | `non-NULL means the pull request was merged, NULL means it was not merged` |
| `Use merged = 1 to identify merged pull requests` | `Use merged_at IS NOT NULL to identify merged pull requests` |
| `State: pre-migration` | `State: post-migration` |

**After updating the document text, update metadata:**

```json
{
  "stale": false,
  "schema_state": "post_migration_synced"
}
```

### Embedding algorithm

Re-embed using the same deterministic hash function used at seed time:

```python
import hashlib, math, re

DIMENSIONS = 64

def embed(text: str) -> list[float]:
    words = re.findall(r"[a-z0-9_]+", text.lower()) or ["empty"]
    tokens = list(words) + [f"{a}|{b}" for a, b in zip(words, words[1:])]
    vector = [0.0] * DIMENSIONS
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        bucket = int.from_bytes(digest[:4], "big") % DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weight = 1.0 + (digest[5] / 255.0)
        vector[bucket] += sign * weight
    magnitude = math.sqrt(sum(v * v for v in vector))
    return [v / magnitude for v in vector] if magnitude else vector
```

This is identical to `deterministic_embedding()` in `db/vectordb/init/seed_vectors.py`.
Using a different algorithm will break retrieval affinity.

---

## Connection settings

All connection parameters come from `agentic_system/config.py` (`settings`):

| Setting | Default |
|---------|---------|
| `clickhouse_host` | `localhost` |
| `clickhouse_port` | `8123` |
| `chroma_host` | `localhost` |
| `chroma_port` | `8000` |
| `clickhouse_database` | `default` |

ChromaDB tenant: `default_tenant`, database: `default_database`.
