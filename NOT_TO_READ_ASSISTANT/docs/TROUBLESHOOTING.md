# Troubleshooting — Ghost Contributors Demo

---

## Infrastructure

### `make up` fails or containers won't start

**Symptoms:** `docker compose` error, containers exit immediately, port conflicts.

**Check Docker:**
```bash
docker info
# Must show the Docker daemon is running
```

**Check for port conflicts:**
```bash
# Ports used: 8123 (ClickHouse HTTP), 9000 (ClickHouse native), 8000 (ChromaDB), 5002 (MLflow)
lsof -ti tcp:8123 tcp:9000 tcp:8000 tcp:5002
```

**Kill conflicting processes and retry:**
```bash
make clean-complete
make up
```

---

### `make seed` hangs or times out

**Symptoms:** The seed script runs but produces no output or exits after a few rows.

The seed script downloads ~5M rows from GitHub Archive. On a slow connection it can take 5–10 minutes. Let it run.

If it genuinely hangs:
```bash
# Restart ClickHouse and retry
docker compose restart clickhouse
make seed
```

---

### ChromaDB is unreachable

**Symptoms:** `ConnectionRefusedError` on port 8000 when seeding vectors or running the agent.

```bash
# Check ChromaDB container is running
docker compose ps chromadb

# Check the health endpoint
curl http://localhost:8000/api/v2/heartbeat

# Restart if needed
docker compose restart chromadb
make seed-vectors
```

---

### MLflow UI is blank or shows no experiments

**Symptoms:** `http://localhost:5002` loads but shows no experiments after running the agent.

The experiment is pre-created on container startup. If it's missing:
```bash
docker compose restart mlflow
```

Then run a query in the TUI — the experiment and run will appear.

---

## TUI / Agent

### TUI launches but returns 0 rows (pre-migration)

This usually means ChromaDB has no vectors, the ClickHouse data isn't seeded, or the `.env` credentials are missing.

**Check in order:**

1. Verify data is seeded:
```bash
# Should return a non-zero count
docker compose exec clickhouse clickhouse-client -q "SELECT count() FROM github_events"
```

2. Verify ChromaDB has collections:
```bash
curl http://localhost:8000/api/v2/tenants/default_tenant/databases/default_database/collections
```

3. Verify `.env` exists with API credentials:
```bash
cat .env | grep -E "OPENAI|AZURE"
```

---

### TUI launches but the agent throws an authentication error

**Symptoms:** Error message in the trace pane mentioning `401`, `Unauthorized`, or `invalid_api_key`.

Check your `.env`:
```bash
# For OpenAI
OPENAI_PROVIDER=openai
OPENAI_API_KEY=sk-...

# For Azure OpenAI
OPENAI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

Restart the TUI after editing `.env` — environment variables are loaded at process start.

---

### TUI output is garbled or the terminal looks broken

The TUI requires a terminal that supports ANSI escape codes and is at least 80 columns wide.

- Make the terminal window wider.
- Avoid running inside a terminal multiplexer that strips color codes.
- On Windows, use WSL — the native command prompt may not render correctly.

---

### `Ctrl+C` doesn't exit the TUI

Use `Ctrl+C` twice, or close the terminal window. The TUI may be in the middle of streaming an agent response.

---

## Migration and Schema-Sync

### `make migrate` fails

**Symptoms:** Script errors out, migration does not complete.

Check that ClickHouse is running and the table exists:
```bash
docker compose exec clickhouse clickhouse-client -q "SHOW TABLES"
```

Check that the table is in the pre-migration state (not already migrated):
```bash
docker compose exec clickhouse clickhouse-client -q "DESCRIBE TABLE github_events"
# Should show 'merged' as UInt8, should NOT show 'merged_at'
```

If already migrated, run rollback first:
```bash
make rollback
make migrate
```

---

### `make validate-schema` reports drift unexpectedly

This means the live ClickHouse schema doesn't match `agentic_system/schema/github_events.yaml`.

**If you just ran `make migrate`** — this is expected. Run `make schema-sync` to fix it.

**If you haven't migrated** — the YAML may be out of sync with the DB. Compare:
```bash
uv run python dev_tools/scripts/clickhouse_introspect.py --table github_events
cat agentic_system/schema/github_events.yaml
```

---

### `make schema-sync` fails mid-run

Run steps individually to find which one fails:
```bash
uv run python dev_tools/scripts/clickhouse_introspect.py --table github_events
uv run python dev_tools/scripts/yaml_patch.py --table github_events --dry-run
uv run python dev_tools/scripts/chroma_patch.py --dry-run
uv run python dev_tools/scripts/prompt_patch.py --dry-run
```

ChromaDB patch failures usually mean ChromaDB is unreachable. Prompt patch failures usually mean the prompt files have already been patched (run `--rollback` first).

---

### Agent still returns 0 rows after `make schema-sync`

1. Confirm validate-schema passes:
```bash
make validate-schema
# Expected: No drift
```

2. Confirm prompt files no longer reference the old predicate:
```bash
grep -r "merged = 1" agentic_system/agents_core/
# Expected: no output
```

3. Confirm ChromaDB chunks are no longer stale:
```bash
curl -s -X POST "http://localhost:8000/api/v2/tenants/default_tenant/databases/default_database/collections/schema_docs/get" \
  -H "Content-Type: application/json" \
  -d '{"include": ["metadatas"]}' | python3 -m json.tool | grep stale
# Expected: no 'true' values
```

4. If everything looks clean but still fails, restart the TUI to reload prompts:
```bash
# Ctrl+C in TUI terminal
uv run python agentic_system/main.py
```

---

### How to fully reset to a clean state

```bash
# Option 1: Rollback schema only (fast)
make rollback

# Option 2: Wipe and re-seed everything (slow, ~5 min)
make reset
make seed
make seed-vectors
```

---

## Tests

### `pytest` fails with import errors

Make sure you are using `uv run`:
```bash
uv run pytest tests/ -m "pre_migration or post_migration or schema_sync"
```

If using plain `python -m pytest`, the project dependencies may not be on the path.

---

### Tests pass but the live agent still fails

Tests use mocked ClickHouse and ChromaDB clients — they do not verify live infrastructure. A passing test suite means the agent logic is correct, not that the services are running.

Run the end-to-end verification to check live services:
```bash
make verify-complete-flow
```

---

## Getting More Help

- Check the session log file: `logs/session_<timestamp>.log`
- MLflow traces at `http://localhost:5002` show exactly what SQL was generated and what rows were returned
- Open an issue at the repository if you encounter a bug not covered here
