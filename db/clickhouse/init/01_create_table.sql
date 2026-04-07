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
