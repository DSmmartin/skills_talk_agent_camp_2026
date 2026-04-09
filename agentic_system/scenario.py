"""
agentic_system/scenario.py

Scenario-specific constants and runner helper for the Ghost Contributors app.
The orchestrator itself is generic — this module holds the default question
and the async run wrapper used by the TUI and CLI.

Run directly:
    python -m agentic_system.scenario
"""

import asyncio
import json

from agents import Runner, RunResult, ToolCallItem, ToolCallOutputItem
from loguru import logger

from agentic_system.config import settings
from agentic_system.setup import setup_openai
from agentic_system.orchestrator import orchestrator

# Full GitHub Archive dataset (default: make seed)
DEFAULT_QUESTION = (
    "Show me repositories where users opened PRs but never got one merged — "
    "the ghost contributors. Focus on kcivicrm/civicrm-core."
)

# Controlled local dataset (make seed LOCAL=1) — 18 rows across 3 repos
LOCAL_QUESTION = (
    "Show me repositories where users opened PRs but never got one merged — "
    "the ghost contributors. Focus on org/repo-alpha, org/repo-beta, and org/repo-gamma."
)


async def run_query(question: str) -> RunResult:
    """Run any question through the orchestrator."""
    logger.info("Run query start")
    logger.debug("Question: {}", question)
    result = Runner.run_streamed(orchestrator, question)

    async for event in result.stream_events():
        if event.type != "run_item_stream_event":
            continue

        item = event.item

        if isinstance(item, ToolCallItem):
            raw = item.raw_item
            tool_name = getattr(raw, "name", "unknown")
            logger.debug("Tool call start: {}", tool_name)

            arguments = getattr(raw, "arguments", None)
            if arguments:
                try:
                    args = json.loads(arguments)
                    logger.debug("Tool call args: {}", args)
                except (json.JSONDecodeError, TypeError):
                    logger.debug("Tool call args (raw): {}", arguments)

        elif isinstance(item, ToolCallOutputItem):
            output = item.output
            tool_name = getattr(item, "tool_name", None)
            if isinstance(output, str):
                try:
                    out = json.loads(output)
                except (json.JSONDecodeError, TypeError):
                    out = output
            else:
                out = output

            if isinstance(out, dict):
                logger.debug(
                    "Tool output tool={} keys={} error={}",
                    tool_name or "unknown",
                    list(out.keys()),
                    out.get("error"),
                )
            else:
                snippet = str(out)[:180].replace("\n", " ")
                logger.debug(
                    "Tool output tool={} snippet={}",
                    tool_name or "unknown",
                    snippet,
                )

    return result


def run_query_sync(question: str) -> RunResult:
    """Synchronous wrapper around run_query for non-async callers (e.g. CLI smoke test)."""
    logger.info("Run query sync start")
    logger.debug("Question: {}", question)
    return asyncio.run(run_query(question))


if __name__ == "__main__":
    setup_openai()

    question = LOCAL_QUESTION if settings.local_seed else DEFAULT_QUESTION

    async def _main() -> None:
        result = await run_query(question)
        logger.info("Run query completed")
        print(result.final_output)

    asyncio.run(_main())
