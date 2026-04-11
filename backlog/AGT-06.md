---
id: AGT-06
name: loguru Setup — File Sink Only, stdout Disabled
epic: Epic 2 - Agentic System (Act 1)
status: [x] Done
summary: Configure loguru to write all logs to a rotating session file and remove the default stdout handler so the Textual TUI owns the terminal.
---

# AGT-06 - loguru Setup — File Sink Only, stdout Disabled

- Epic: Epic 2 - Agentic System (Act 1)
- Priority: P0
- Estimate: S
- Status: [ ] Todo
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L632)

## Objective

Configure loguru so all application log output goes to a rotating file sink and stdout is completely suppressed, allowing the Textual TUI to own the terminal without interference.

## Description

Textual takes over the terminal for rendering. Any stdout output from loguru (or other libraries) will corrupt the TUI display. This task removes loguru's default handler and adds a single file sink that rotates per session. All agent code, tool calls, and orchestrator activity will log to `logs/session_{time}.log` for post-session review without disturbing the live UI.

## Scope

- Create `agentic_system/observability/logger.py` with loguru configuration.
- Remove the default loguru stdout handler via `logger.remove()`.
- Add a file sink at `logs/session_{time}.log` with per-session rotation, DEBUG level, and a structured format.
- Ensure the logger module is imported early in `agentic_system/main.py` so suppression is applied before any agent code runs.

## Out Of Scope

- MLflow tracing (AGT-07).
- Structured log parsing or log aggregation.
- Log shipping to external systems.
- Any stdout logging path — stdout must remain fully suppressed for the TUI.

## Deliverables

- `agentic_system/observability/logger.py` — loguru configured with file-only sink and stdout removed.

## Acceptance Criteria

- `logger.remove()` is called before any `logger.add()` to strip the default stdout handler.
- A file sink is added at `logs/session_{time}.log` with `rotation="1 session"` and `level="DEBUG"`.
- Log format includes `{time}`, `{level}`, `{name}`, and `{message}`.
- No log output appears on stdout when the TUI is running.
- `logs/` directory is created automatically if it does not exist (or is pre-created as part of repo scaffolding).

## Dependencies

- AGT-08: `agentic_system/main.py` must import `agentic_system.observability.logger` before other agent modules to ensure stdout suppression is applied first.

## Assumptions

- `logs/` directory either exists or `loguru` creates it on first write.
- The format string from the backlog architecture section is used verbatim: `"{time} | {level} | {name} | {message}"`.

## Notes

- This is a prerequisite for a stable TUI demo — must be imported first in `main.py`.
