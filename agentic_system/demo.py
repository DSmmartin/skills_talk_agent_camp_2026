"""
agentic_system/demo.py

Demo-specific constants and runner helper for the Ghost Contributors talk.
The orchestrator itself is generic — this module holds the demo question
and the async run wrapper used by the TUI and CLI.

Run directly:
    python -m agentic_system.demo
"""

import asyncio
import json

from agents import Runner, RunResult, ToolCallItem, ToolCallOutputItem
from loguru import logger

from agentic_system.setup import setup_openai
from agentic_system.orchestrator import orchestrator

DEMO_QUESTION = (
    "Show me repositories where users opened PRs but never got one merged — "
    "the ghost contributors. Focus on kcivicrm/civicrm-core."
)


async def run_query(question: str) -> RunResult:
    """Run any question through the orchestrator."""
    logger.info("Demo run_query start")
    logger.debug("Demo question: {}", question)
    result = Runner.run_streamed(orchestrator, question)

    async for event in result.stream_events():
        if event.type != "run_item_stream_event":
            continue

        item = event.item

        if isinstance(item, ToolCallItem):
            raw = item.raw_item
            tool_name = getattr(raw, "name", "unknown")
            logger.debug("Demo tool call start: {}", tool_name)

            arguments = getattr(raw, "arguments", None)
            if arguments:
                try:
                    args = json.loads(arguments)
                    logger.debug("Demo tool call args: {}", args)
                except (json.JSONDecodeError, TypeError):
                    logger.debug("Demo tool call args (raw): {}", arguments)

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
                    "Demo tool output tool={} keys={} error={}",
                    tool_name or "unknown",
                    list(out.keys()),
                    out.get("error"),
                )
            else:
                snippet = str(out)[:180].replace("\n", " ")
                logger.debug(
                    "Demo tool output tool={} snippet={}",
                    tool_name or "unknown",
                    snippet,
                )

    return result


def run_query_sync(question: str) -> RunResult:
    """Synchronous wrapper around run_query for non-async callers (e.g. CLI smoke test)."""
    logger.info("Demo run_query_sync start")
    logger.debug("Demo question: {}", question)
    return asyncio.run(run_query(question))


if __name__ == "__main__":
    setup_openai()

    async def _main() -> None:
        result = await run_query(DEMO_QUESTION)
        logger.info("Demo run_query completed")
        print(result.final_output)

    asyncio.run(_main())
