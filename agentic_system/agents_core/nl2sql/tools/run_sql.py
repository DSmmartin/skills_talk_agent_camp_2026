import json

import clickhouse_connect
from agents import function_tool
from loguru import logger

from agentic_system.config import settings


def _get_client() -> clickhouse_connect.driver.client.Client:
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


def run_sql_core(sql: str) -> str:
    """Execute a ClickHouse SQL query and return the results along with the SQL used.

    Core logic — callable directly in scripts and tests without an agent context.

    Args:
        sql: Valid ClickHouse SQL query to execute against the github_events table.

    Returns:
        A JSON string containing the SQL executed, row count, and up to 50 result rows.
    """
    logger.info("run_sql start")
    logger.debug("run_sql SQL: {}", sql.strip())
    try:
        client = _get_client()
    except Exception as exc:
        logger.error(
            "ClickHouse connection failed ({}:{}): {}",
            settings.clickhouse_host,
            settings.clickhouse_port,
            exc,
        )
        return json.dumps({
            "error": "connection_failed",
            "detail": (
                f"Could not connect to ClickHouse at "
                f"{settings.clickhouse_host}:{settings.clickhouse_port}. "
                f"Reason: {exc}"
            ),
            "sql": sql.strip(),
            "row_count": 0,
            "rows": [],
        })

    try:
        result = client.query(sql)
        rows = list(result.named_results())
        row_count = len(rows)
        logger.info("run_sql returned {} rows", row_count)
        return json.dumps({
            "sql": sql.strip(),
            "row_count": row_count,
            "rows": rows[:50],
        }, default=str)

    except Exception as exc:
        logger.error("ClickHouse query failed: {}\nSQL: {}", exc, sql.strip())
        return json.dumps({
            "error": "query_failed",
            "detail": str(exc),
            "sql": sql.strip(),
            "row_count": 0,
            "rows": [],
        })


@function_tool
def run_sql(sql: str) -> str:
    """Execute a ClickHouse SQL query and return the results along with the SQL used.

    Args:
        sql: Valid ClickHouse SQL query to execute against the github_events table.

    Returns:
        A JSON string containing the SQL executed, row count, and up to 50 result rows.
    """
    return run_sql_core(sql)
