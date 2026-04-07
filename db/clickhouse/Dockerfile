FROM clickhouse/clickhouse-server:latest

# Persist ClickHouse data at the canonical server data path.
VOLUME ["/var/lib/clickhouse"]

# Keep the build context ready for follow-up tasks that will add init SQL
# and config files without changing the image structure here.
WORKDIR /var/lib/clickhouse
