"""
agentic_system/memory.py

Session-scoped conversation memory for the orchestrator.

The OpenAI Agents SDK represents conversation history as a flat list of
input items (TResponseInputItem). After each run, result.to_input_list()
returns the full history — original input plus all assistant turns, tool
calls, and tool outputs.  Passing that list as the *input* of the next run
gives the orchestrator full context of prior exchanges.

Usage:
    memory = ConversationMemory()

    # First turn
    result = Runner.run_streamed(agent, memory.build_input("Who are ghost contributors?"))
    ...await result...
    memory.update(result)

    # Second turn — agent sees the full prior conversation
    result = Runner.run_streamed(agent, memory.build_input("Show me more from that repo"))
    ...await result...
    memory.update(result)

    # Reset at session end or on user request
    memory.clear()
"""

from __future__ import annotations

from agents import TResponseInputItem


class ConversationMemory:
    """Holds the accumulated turn history for one chat session."""

    def __init__(self) -> None:
        self._history: list[TResponseInputItem] = []

    # ── Public interface ───────────────────────────────────────────────

    @property
    def turn_count(self) -> int:
        """Number of completed user turns recorded in history."""
        return sum(
            1
            for item in self._history
            if isinstance(item, dict) and item.get("role") == "user"
        )

    @property
    def is_empty(self) -> bool:
        return not self._history

    def build_input(self, question: str) -> str | list[TResponseInputItem]:
        """Return the input to pass to Runner.run_streamed.

        On the first turn returns the bare question string (no overhead).
        On subsequent turns returns the accumulated history with the new
        user message appended so the agent sees the full conversation.
        """
        if not self._history:
            return question
        return self._history + [{"role": "user", "content": question}]

    def update(self, result: object) -> None:
        """Capture history from a completed RunResult or RunResultStreaming."""
        self._history = result.to_input_list()  # type: ignore[attr-defined]

    def clear(self) -> None:
        """Discard all history (start a new session)."""
        self._history.clear()
