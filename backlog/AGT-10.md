---
id: AGT-10
name: Conversation Memory — Session-Scoped History via to_input_list()
epic: Epic 2 - Agentic System (Act 1)
status: [x] Done
summary: Add session-scoped conversation memory to the TUI so the agent can answer follow-up questions with full prior context.
---

# AGT-10 - Conversation Memory — Session-Scoped History via to_input_list()

- Epic: Epic 2 - Agentic System (Act 1)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L108)

## Objective

Allow the agent to answer follow-up questions without the user repeating context. Each new question is submitted with the full prior turn history so the LLM has complete conversational context.

## Description

The OpenAI Agents SDK captures the full input+output history of each run via `result.to_input_list()`. `ConversationMemory` wraps this pattern: it stores the history after each run and prepends it to the next input. The TUI calls `memory.build_input(question)` before running the agent and `memory.update(result)` after. `Ctrl+L` clears the chat and resets memory.

## Scope

- Create `agentic_system/memory.py` with `ConversationMemory` class.
- Wire `ConversationMemory` into `agentic_system/tui/app.py`.
- Display memory status in the trace pane separator: `─── Run 2  [mem: 1 turn] ───`.
- `Ctrl+L` resets both `_memory` and `_run_count` and prints a "Memory cleared" hint.

## Out Of Scope

- Persistent memory across TUI sessions (session-scoped only).
- Memory summarisation or compression.
- Exporting conversation history.

## Deliverables

- `agentic_system/memory.py` — `ConversationMemory` with `build_input()`, `update()`, `clear()`, `turn_count`, `is_empty`.
- Updated `agentic_system/tui/app.py` — memory instantiated on mount, wired into `_run_query` and `action_clear_chat`.

## Acceptance Criteria

- Second question in same session references prior answer without user repeating context.
- Trace pane separator shows `[mem: N turn(s)]` from the second run onward.
- `Ctrl+L` clears both panes, resets run count and memory, prints confirmation hint.
- `ConversationMemory` is importable standalone (no TUI dependency).

## Dependencies

- AGT-05: TUI in place.
- AGT-08: `main.py` entry point available.
- AGT-09: End-to-end Act 1 verified.

## Assumptions

- `Runner.run_streamed()` returns an object with `to_input_list()` that captures the full turn history including tool calls and outputs.
- Session memory is sufficient; no persistence required between TUI restarts.

## Verification

```bash
uv run python -c "
from agentic_system.memory import ConversationMemory
m = ConversationMemory()
assert m.is_empty
assert m.turn_count == 0
assert m.build_input('hello') == 'hello'
print('ConversationMemory: OK')
"
```

## Notes

- Completed 2026-04-08.
- `to_input_list()` returns `list[TResponseInputItem]` — a union of user/assistant/tool dicts. Prepending it to the next message gives the model full context.
- The `_run_count` counter on the TUI app is intentionally separate from `memory.turn_count` so `Ctrl+L` resets the display numbering independently.
