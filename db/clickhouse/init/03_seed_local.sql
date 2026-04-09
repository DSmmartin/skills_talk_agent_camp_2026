-- Local dummy seed for offline fallback.
-- 18 rows across 3 repos, pre-migration schema (merged UInt8).
--
-- Ghost contributors (merged=0 on every row): ghost-user-1, ghost-user-2, ghost-user-3, ghost-user-4
-- Regular contributors (at least one merged=1):  alice, bob, carol, dave
--
-- DROP + CREATE instead of TRUNCATE to clear any ALTER TABLE UPDATE mutations
-- left by a previous `make migrate` run. ClickHouse mutations persist at table
-- level and apply to newly inserted parts even after TRUNCATE.

DROP TABLE IF EXISTS github_events;

CREATE TABLE github_events (
    event_type   String,
    action       LowCardinality(String),
    actor_login  String,
    repo_name    String,
    created_at   DateTime,
    merged       UInt8,
    number       UInt32,
    title        String
) ENGINE = MergeTree()
ORDER BY (event_type, repo_name, created_at);

INSERT INTO github_events (event_type, action, actor_login, repo_name, created_at, merged, number, title) VALUES
('PullRequestEvent', 'opened', 'alice',        'org/repo-alpha', '2024-01-10 09:00:00', 0, 1,  'Add login endpoint'),
('PullRequestEvent', 'closed', 'alice',        'org/repo-alpha', '2024-01-11 14:00:00', 1, 1,  'Add login endpoint'),
('PullRequestEvent', 'closed', 'bob',          'org/repo-alpha', '2024-01-12 11:30:00', 1, 2,  'Fix null pointer in auth'),
('PullRequestEvent', 'opened', 'ghost-user-1', 'org/repo-alpha', '2024-01-15 08:00:00', 0, 3,  'Refactor session manager'),
('PullRequestEvent', 'closed', 'ghost-user-1', 'org/repo-alpha', '2024-01-16 10:00:00', 0, 3,  'Refactor session manager'),
('PullRequestEvent', 'opened', 'ghost-user-1', 'org/repo-alpha', '2024-02-01 09:15:00', 0, 4,  'Add retry logic'),
('PullRequestEvent', 'closed', 'ghost-user-1', 'org/repo-alpha', '2024-02-03 16:45:00', 0, 4,  'Add retry logic'),
('PullRequestEvent', 'closed', 'carol',        'org/repo-beta',  '2024-01-20 13:00:00', 1, 5,  'Improve query performance'),
('PullRequestEvent', 'closed', 'carol',        'org/repo-beta',  '2024-02-10 15:30:00', 1, 6,  'Add index on created_at'),
('PullRequestEvent', 'opened', 'ghost-user-2', 'org/repo-beta',  '2024-01-22 10:00:00', 0, 7,  'Migrate to async driver'),
('PullRequestEvent', 'closed', 'ghost-user-2', 'org/repo-beta',  '2024-01-24 11:00:00', 0, 7,  'Migrate to async driver'),
('PullRequestEvent', 'opened', 'ghost-user-3', 'org/repo-beta',  '2024-02-05 09:00:00', 0, 8,  'Add caching layer'),
('PullRequestEvent', 'closed', 'ghost-user-3', 'org/repo-beta',  '2024-02-07 17:00:00', 0, 8,  'Add caching layer'),
('PullRequestEvent', 'closed', 'dave',         'org/repo-gamma', '2024-01-18 12:00:00', 1, 9,  'Update dependencies'),
('PullRequestEvent', 'closed', 'dave',         'org/repo-gamma', '2024-03-01 10:00:00', 1, 10, 'Bump clickhouse-driver to 0.2.9'),
('PullRequestEvent', 'opened', 'ghost-user-4', 'org/repo-gamma', '2024-01-25 08:30:00', 0, 11, 'Add Prometheus metrics'),
('PullRequestEvent', 'closed', 'ghost-user-4', 'org/repo-gamma', '2024-01-27 09:00:00', 0, 11, 'Add Prometheus metrics'),
('PullRequestEvent', 'opened', 'ghost-user-4', 'org/repo-gamma', '2024-02-14 11:00:00', 0, 12, 'Switch to structured logging');
