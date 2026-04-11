---
id: MIG-05
name: Verify Silent Wrong Answer After Migration
epic: Epic 3 - Migration Scripts (Act 2)
status: [x] Done
summary: Confirm that after migration the agent returns 0 rows with no exception — the intended Act 2 silent failure.
---

# MIG-05 - Verify Silent Wrong Answer After Migration

- Epic: Epic 3 - Migration Scripts (Act 2)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L120)

## Objective

Confirm the Act 2 broken state produces the exact demo effect: the old SQL (`merged = 1`) executes without error and returns 0 rows — a silent, plausible-looking wrong answer.

## Description

After `make migrate`, the agent's prompts still instruct it to write `WHERE merged = 1`. That SQL is syntactically valid and runs successfully against the migrated schema (the `merged` column still exists, now all zeros). The result is 0 ghost contributors — which looks like a valid answer, not an error.

This distinguishes the failure from a noisy failure (exception) — the presenter can say "the system ran, produced a result, but the result is wrong, and nothing flagged it."

## Scope

- Verify at the SQL level: `WHERE merged = 1` returns 0, no exception.
- Verify the correct new query: `WHERE merged_at IS NOT NULL` returns ~1.6M.
- Document the expected demo talking point.

## Out Of Scope

- Running the full TUI / LLM pipeline (that is manual demo verification).
- Automating the LLM response content check.

## Deliverables

- Verification commands and expected output documented here.

## Acceptance Criteria

- `SELECT count() FROM github_events WHERE event_type='PullRequestEvent' AND merged = 1` returns 0 (no exception).
- `SELECT count() FROM github_events WHERE event_type='PullRequestEvent' AND merged_at IS NOT NULL` returns ~1.6M.

## Dependencies

- MIG-01: Migration must have been run.

## Verification

```bash
make migrate
uv run python -c "
import clickhouse_connect
c = clickhouse_connect.get_client(host='localhost', port=8123)
r1 = c.query(\"SELECT count() FROM github_events WHERE event_type='PullRequestEvent' AND merged = 1\")
r2 = c.query(\"SELECT count() FROM github_events WHERE event_type='PullRequestEvent' AND merged_at IS NOT NULL\")
print('Old predicate (merged=1):         ', r1.result_rows[0][0], '<-- silent 0 rows')
print('New predicate (merged_at IS NOT NULL):', r2.result_rows[0][0], '<-- correct count')
"
```

Expected (verified 2026-04-08):
```
Old predicate (merged=1):          0 <-- silent 0 rows
New predicate (merged_at IS NOT NULL): 1610448 <-- correct count
```

## Notes

- Completed 2026-04-08.
- Demo talking point: "The query ran. No error. The agent says there are 0 ghost contributors. That looks like a valid answer. But it's wrong — and nothing in the system flagged it."
- The zeroing approach in MIG-01 (vs DROP COLUMN) is what makes this silent. DROP would cause `UNKNOWN_IDENTIFIER` and expose the root cause immediately.
