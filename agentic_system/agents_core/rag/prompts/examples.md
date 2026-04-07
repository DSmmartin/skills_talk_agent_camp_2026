# AgentRAG — Few-Shot Examples

## Example 1

**User question:** Who are ghost contributors on kubernetes/kubernetes?

**Retrieved context:**
```
Field: merged (UInt8)
Type: UInt8
Semantics: 1 if the pull request was merged, 0 if it was closed without merging.
Usage: Use merged = 1 to filter merged PRs, merged = 0 for unmerged/rejected PRs.

Field: action (LowCardinality(String))
Type: LowCardinality(String)
Semantics: The PR lifecycle event. Values: 'opened', 'closed', 'reopened', 'synchronize'.
Usage: Use action = 'opened' to count PRs submitted, action = 'closed' for closed PRs.

Example SQL (ghost contributors):
SELECT repo_name, actor_login,
       countIf(action = 'opened') AS prs_opened,
       countIf(action = 'closed' AND merged = 1) AS prs_merged
FROM github_events
WHERE event_type = 'PullRequestEvent'
GROUP BY repo_name, actor_login
HAVING prs_opened > 0 AND prs_merged = 0
ORDER BY prs_opened DESC
LIMIT 50;
```

---

## Example 2

**User question:** How long do unmerged PRs stay open on average?

**Retrieved context:**
```
Field: merged (UInt8)
Type: UInt8
Semantics: 0 = PR was closed without merging. Use merged = 0 to filter rejected PRs.

Field: created_at (DateTime)
Type: DateTime
Semantics: Timestamp when the event occurred.
Usage: Use avgIf(created_at, ...) to compute time-based aggregates per action.

Example SQL (unmerged PR dwell time):
SELECT repo_name, actor_login,
       countIf(action = 'opened') AS prs_opened,
       avgIf(created_at, action = 'closed' AND merged = 0) AS avg_close_time
FROM github_events
WHERE event_type = 'PullRequestEvent'
  AND merged = 0
GROUP BY repo_name, actor_login
HAVING prs_opened >= 3
ORDER BY prs_opened DESC
LIMIT 30;
```
