# Schema Reference — GitHub Archive `github_events` Table

## Overview

The `github_events` table in ClickHouse holds approximately 5 million rows of pull request events sourced from the [GitHub Archive](https://www.gharchive.org/). The dataset is filtered to `PullRequestEvent` rows only.

---

## Pre-Migration Schema

This is the schema after `make seed` and before `make migrate`.

| Column | Type | Description |
|--------|------|-------------|
| `event_type` | `String` | GitHub event type — always `PullRequestEvent` in this dataset |
| `action` | `LowCardinality(String)` | Action within the event: `opened`, `closed`, `reopened`, `synchronize` |
| `actor_login` | `String` | GitHub username of the actor who triggered the event |
| `repo_name` | `String` | Full repository name in `owner/repo` format (e.g. `kubernetes/kubernetes`) |
| `created_at` | `DateTime` | UTC timestamp when the event occurred |
| `merged` | `UInt8` | `1` if the pull request was merged, `0` if not. Use `merged = 1` to filter merged PRs |
| `number` | `UInt32` | Pull request number within the repository |
| `title` | `String` | Title of the pull request |

---

## Post-Migration Schema

This is the schema after `make migrate` (Act 2 of the demo).

| Column | Type | Description |
|--------|------|-------------|
| `event_type` | `String` | Same as pre-migration |
| `action` | `LowCardinality(String)` | Same as pre-migration |
| `actor_login` | `String` | Same as pre-migration |
| `repo_name` | `String` | Same as pre-migration |
| `created_at` | `DateTime` | Same as pre-migration |
| `merged` | `UInt8` | Zeroed out (all values = 0). Kept for column compatibility. Do not use for filtering |
| `number` | `UInt32` | Same as pre-migration |
| `title` | `String` | Same as pre-migration |
| `merged_at` | `Nullable(DateTime)` | Added in migration. Non-null if the PR was merged, null if not. Use `merged_at IS NOT NULL` to filter merged PRs |

---

## Migration Summary

| Field | Before | After | SQL predicate change |
|-------|--------|-------|---------------------|
| `merged` | `UInt8` (0 or 1) | `UInt8` (zeroed, always 0) | `merged = 1` → **no longer works** |
| `merged_at` | *(not present)* | `Nullable(DateTime)` | *(new)* `merged_at IS NOT NULL` |

The migration is the core of Act 2. All four system layers encode the pre-migration field name, so the rename causes a **silent failure**: the agent generates SQL with `merged = 1` which now matches zero rows, with no exception raised.

---

## The Ghost Contributor Query

The demo question targets the following pattern:

> *"Show me repositories where users opened PRs but never got one merged — the ghost contributors"*

### Pre-migration SQL

```sql
SELECT
    repo_name,
    actor_login,
    count(*) AS total_prs
FROM github_events
WHERE
    event_type = 'PullRequestEvent'
    AND action = 'opened'
    AND actor_login NOT IN (
        SELECT DISTINCT actor_login
        FROM github_events
        WHERE event_type = 'PullRequestEvent'
          AND merged = 1
    )
GROUP BY repo_name, actor_login
ORDER BY total_prs DESC
LIMIT 20
```

### Post-migration SQL (after schema-sync)

```sql
SELECT
    repo_name,
    actor_login,
    count(*) AS total_prs
FROM github_events
WHERE
    event_type = 'PullRequestEvent'
    AND action = 'opened'
    AND actor_login NOT IN (
        SELECT DISTINCT actor_login
        FROM github_events
        WHERE event_type = 'PullRequestEvent'
          AND merged_at IS NOT NULL
    )
GROUP BY repo_name, actor_login
ORDER BY total_prs DESC
LIMIT 20
```

---

## ClickHouse Connection Details

| Setting | Default |
|---------|---------|
| Host | `localhost` |
| HTTP port | `8123` |
| Native port | `9000` |
| User | `default` |
| Password | *(empty)* |
| Database | `default` |

Override any value in `.env`. See `.env.example` for all variables.

---

## Inspecting the Live Schema

```bash
# Via the introspection script
uv run python dev_tools/scripts/clickhouse_introspect.py --table github_events

# Via validate-schema (diffs live DB against YAML contract)
uv run python scripts/validate_schema.py

# Via Makefile
make validate-schema
```

---

## YAML Contract

The machine-readable schema contract lives at:

```
agentic_system/schema/github_events.yaml
```

This file is the authoritative field definition used by `schema_sync.py` to detect drift and drive patches to the NL2SQL prompt, RAG prompt, and ChromaDB chunks. After `make schema-sync`, this file reflects the post-migration schema.

---

## ChromaDB Collections

| Collection | Contents |
|------------|----------|
| `schema_docs` | Field descriptions for RAG retrieval — one chunk per field |
| `qa_examples` | Example question-to-SQL pairs for few-shot retrieval |

Chunks that encode pre-migration field names are marked `stale: true` in their metadata after `make migrate`. `schema_sync.py` re-patches and re-embeds them.
