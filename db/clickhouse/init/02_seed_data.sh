#!/bin/sh

set -eu

CLICKHOUSE_CLIENT_BIN="${CLICKHOUSE_CLIENT_BIN:-clickhouse-client}"
CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-9000}"
CLICKHOUSE_USER="${CLICKHOUSE_USER:-default}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-}"
CLICKHOUSE_DATABASE="${CLICKHOUSE_DATABASE:-default}"
TARGET_TABLE="${TARGET_TABLE:-github_events}"
PR_EVENT_TYPE="${PR_EVENT_TYPE:-PullRequestEvent}"
GITHUB_ARCHIVE_TARGET_ROWS="${GITHUB_ARCHIVE_TARGET_ROWS:-5000000}"
GITHUB_ARCHIVE_SOURCE_BASE_URL="${GITHUB_ARCHIVE_SOURCE_BASE_URL:-https://clickhouse-public-datasets.s3.amazonaws.com/github_events/partitioned_json}"
GITHUB_ARCHIVE_SOURCE_SUFFIXES="${GITHUB_ARCHIVE_SOURCE_SUFFIXES:-aa ab ac ad ae af ag}"
TRUNCATE_BEFORE_LOAD="${TRUNCATE_BEFORE_LOAD:-1}"

case "${GITHUB_ARCHIVE_TARGET_ROWS}" in
    ''|*[!0-9]*)
        echo "GITHUB_ARCHIVE_TARGET_ROWS must be a positive integer" >&2
        exit 1
        ;;
esac

if [ "${GITHUB_ARCHIVE_TARGET_ROWS}" -le 0 ]; then
    echo "GITHUB_ARCHIVE_TARGET_ROWS must be greater than zero" >&2
    exit 1
fi

client() {
    if [ -n "${CLICKHOUSE_PASSWORD}" ]; then
        "${CLICKHOUSE_CLIENT_BIN}" \
            --host "${CLICKHOUSE_HOST}" \
            --port "${CLICKHOUSE_PORT}" \
            --user "${CLICKHOUSE_USER}" \
            --password "${CLICKHOUSE_PASSWORD}" \
            --database "${CLICKHOUSE_DATABASE}" \
            "$@"
    else
        "${CLICKHOUSE_CLIENT_BIN}" \
            --host "${CLICKHOUSE_HOST}" \
            --port "${CLICKHOUSE_PORT}" \
            --user "${CLICKHOUSE_USER}" \
            --database "${CLICKHOUSE_DATABASE}" \
            "$@"
    fi
}

tmp_query_file="$(mktemp)"

cleanup() {
    rm -f "${tmp_query_file}"
}

trap cleanup EXIT INT TERM

if [ "${TRUNCATE_BEFORE_LOAD}" = "1" ]; then
    echo "Truncating ${TARGET_TABLE} before loading seed data"
    client --query "TRUNCATE TABLE ${TARGET_TABLE}"
fi

initial_rows="$(client --query "SELECT count() FROM ${TARGET_TABLE}")"
echo "Initial row count in ${TARGET_TABLE}: ${initial_rows}"
echo "Preparing pull request sample load from suffixes: ${GITHUB_ARCHIVE_SOURCE_SUFFIXES}"

cat > "${tmp_query_file}" <<EOF
INSERT INTO ${TARGET_TABLE} (
    event_type,
    action,
    actor_login,
    repo_name,
    created_at,
    merged,
    number,
    title
)
SELECT
    event_type,
    action,
    actor_login,
    repo_name,
    created_at,
    merged,
    number,
    title
FROM (
EOF

first_suffix=1
for suffix in ${GITHUB_ARCHIVE_SOURCE_SUFFIXES}; do
    if [ "${first_suffix}" -eq 0 ]; then
        printf '\nUNION ALL\n\n' >> "${tmp_query_file}"
    fi

    cat >> "${tmp_query_file}" <<EOF
SELECT
    event_type,
    action,
    actor_login,
    repo_name,
    parsed_created_at AS created_at,
    merged,
    number,
    title
FROM (
    SELECT
        ifNull(event_type, '${PR_EVENT_TYPE}') AS event_type,
        ifNull(action, '') AS action,
        ifNull(actor_login, '') AS actor_login,
        ifNull(repo_name, '') AS repo_name,
        parseDateTimeBestEffortOrNull(ifNull(created_at, '')) AS parsed_created_at,
        toUInt8(greatest(ifNull(merged, 0), 0)) AS merged,
        toUInt32(greatest(ifNull(number, 0), 0)) AS number,
        ifNull(title, '') AS title
    FROM s3(
        '${GITHUB_ARCHIVE_SOURCE_BASE_URL}/github_events_${suffix}.gz',
        'JSONEachRow',
        'event_type Nullable(String), action Nullable(String), actor_login Nullable(String), repo_name Nullable(String), created_at Nullable(String), merged Nullable(Int64), number Nullable(Int64), title Nullable(String)'
    )
    WHERE event_type = '${PR_EVENT_TYPE}'
)
WHERE parsed_created_at IS NOT NULL
EOF

    first_suffix=0
done

cat >> "${tmp_query_file}" <<EOF
)
LIMIT ${GITHUB_ARCHIVE_TARGET_ROWS}
SETTINGS input_format_skip_unknown_fields = 1
EOF

echo "Loading up to ${GITHUB_ARCHIVE_TARGET_ROWS} pull request rows into ${TARGET_TABLE}"
client --multiquery < "${tmp_query_file}"

final_rows="$(client --query "SELECT count() FROM ${TARGET_TABLE}")"
inserted_rows=$((final_rows - initial_rows))

echo "Final row count in ${TARGET_TABLE}: ${final_rows}"
echo "Rows inserted during this run: ${inserted_rows}"

if [ "${final_rows}" -lt "${GITHUB_ARCHIVE_TARGET_ROWS}" ]; then
    echo "Warning: loaded fewer rows than requested target ${GITHUB_ARCHIVE_TARGET_ROWS}" >&2
fi
