"""
scripts/debug_run_sql.py

Developer tool: run the ClickHouse tool core logic directly without an agent context.

Usage:
    python scripts/debug_run_sql.py
    python scripts/debug_run_sql.py "SELECT count() FROM github_events"
"""

import json
import sys
from pathlib import Path

# Make the project root importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentic_system.agents_core.nl2sql.tools.run_sql import run_sql_core
from agentic_system.config import settings

DEFAULT_SQL = "SELECT 1 AS ping"


def main() -> None:
    sql = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SQL

    print(f"ClickHouse  {settings.clickhouse_host}:{settings.clickhouse_port}  "
          f"db={settings.clickhouse_database}  user={settings.clickhouse_user}")
    print(f"SQL: {sql}\n")

    raw = run_sql_core(sql)
    result = json.loads(raw)

    if "error" in result:
        print(f"[ERROR] {result['error']}: {result['detail']}")
        sys.exit(1)

    print(f"row_count: {result['row_count']}")
    for row in result["rows"]:
        print(row)


if __name__ == "__main__":
    main()
