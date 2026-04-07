# AgentNL2SQL — Few-Shot SQL Examples

## Example 1

**Question:** Who are ghost contributors on civicrm/civicrm-core?

**Note:** `kubernetes/kubernetes` is not in this dataset partition. Use the repos listed
in the system prompt. When asked about an absent repo, explain this and pivot to a
well-represented one like `civicrm/civicrm-core`.

**Bot-filter rule:** always exclude automation accounts from contributor analysis.

**Schema context provided:**
- `merged UInt8` — 1 if merged, 0 if closed without merging
- `action LowCardinality(String)` — 'opened', 'closed', 'reopened'
- `actor_login String` — GitHub username
- `repo_name String` — full repository name

**SQL generated:**
```sql
SELECT
    repo_name,
    actor_login,
    countIf(action = 'opened')                  AS prs_opened,
    countIf(action = 'closed' AND merged = 1)   AS prs_merged
FROM github_events
WHERE event_type = 'PullRequestEvent'
  AND repo_name = 'civicrm/civicrm-core'
  AND actor_login NOT LIKE '%[bot]%'
  AND actor_login NOT LIKE '%-bot%'
GROUP BY repo_name, actor_login
HAVING prs_opened > 0 AND prs_merged = 0
ORDER BY prs_opened DESC
LIMIT 50;
```

---

## Example 2

**Question:** How long do unmerged PRs stay open on average?

**Schema context provided:**
- `merged UInt8` — 0 for PRs closed without merging
- `created_at DateTime` — timestamp of the event
- `action LowCardinality(String)` — 'opened', 'closed'

**SQL generated:**
```sql
SELECT
    repo_name,
    actor_login,
    countIf(action = 'opened')                          AS prs_opened,
    avgIf(created_at, action = 'closed' AND merged = 0) AS avg_close_time
FROM github_events
WHERE event_type = 'PullRequestEvent'
  AND merged = 0
GROUP BY repo_name, actor_login
HAVING prs_opened >= 3
ORDER BY prs_opened DESC
LIMIT 30;
```

---

## Example 3

**Question:** Which repos have the most ghost contributors overall?

**SQL generated:**
```sql
SELECT
    repo_name,
    countDistinctIf(actor_login, action = 'opened')                 AS total_contributors,
    countDistinctIf(actor_login,
        action = 'opened'
        AND actor_login NOT IN (
            SELECT actor_login FROM github_events
            WHERE event_type = 'PullRequestEvent'
              AND action = 'closed' AND merged = 1
        )
    )                                                                AS ghost_contributors
FROM github_events
WHERE event_type = 'PullRequestEvent'
GROUP BY repo_name
HAVING ghost_contributors > 0
ORDER BY ghost_contributors DESC
LIMIT 20;
```

---

## Example 4

**Question:** What was the PR rejection rate per year?

**Gotchas demonstrated:**
- Aliases use `_count`/`_pct` suffixes — `AS merged` would clash with the `merged` column and cause error 184.
- `sum(merged)` / `sum(1 - merged)` avoids nesting `countIf` inside `round()`, which also triggers error 184.
- No `now()` or relative intervals — the dataset ends 2022-03-12, so `now()` returns 2026 and relative filters silently return 0 rows.

**SQL generated:**
```sql
SELECT
    toYear(created_at)                             AS yr,
    sum(merged)                                    AS merged_count,
    sum(1 - merged)                                AS rejected_count,
    round(sum(1 - merged) / count() * 100, 1)     AS rejection_rate_pct
FROM github_events
WHERE event_type = 'PullRequestEvent'
  AND action = 'closed'
GROUP BY yr
ORDER BY yr;
```

---

## Example 5

**Question:** What is the monthly PR volume trend for the most recent year?

**Gotcha demonstrated:** use the last full year in the dataset (`2021`) — never `now() - INTERVAL`.

**SQL generated:**
```sql
SELECT
    toStartOfMonth(created_at)  AS month,
    count()                     AS prs_opened
FROM github_events
WHERE event_type = 'PullRequestEvent'
  AND action = 'opened'
  AND toYear(created_at) = 2021
GROUP BY month
ORDER BY month;
```
