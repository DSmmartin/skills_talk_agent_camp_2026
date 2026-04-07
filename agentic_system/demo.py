"""
agentic_system/demo.py

Demo-specific constants and runner helper for the Ghost Contributors talk.
The orchestrator itself is generic — this module holds the demo question
and the async run wrapper used by the TUI and CLI.

Run directly:
    python -m agentic_system.demo
"""

import asyncio

from agents import Runner, RunResult

from agentic_system.setup import setup_openai
from agentic_system.orchestrator import orchestrator

DEMO_QUESTION = (
    "Show me repositories where users opened PRs but never got one merged — "
    "the ghost contributors. Focus on kcivicrm/civicrm-core."
)


async def run_query(question: str) -> RunResult:
    """Run any question through the orchestrator."""
    return await Runner.run(orchestrator, question)


def run_query_sync(question: str) -> RunResult:
    """Synchronous wrapper around run_query for non-async callers (e.g. CLI smoke test)."""
    return asyncio.run(run_query(question))


if __name__ == "__main__":
    setup_openai()

    async def _main() -> None:
        result = await run_query(DEMO_QUESTION)
        print(result.final_output)

    asyncio.run(_main())
