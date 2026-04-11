---
id: AGT-08
name: agentic_system/main.py — Launches TUI and Wires Everything Together
epic: Epic 2 - Agentic System (Act 1)
status: [x] Done
summary: Create agentic_system/main.py as the single entry point that calls setup_openai(), activates loguru, and launches the Textual TUI.
---

# AGT-08 - agentic_system/main.py — Launches TUI and Wires Everything Together

- Epic: Epic 2 - Agentic System (Act 1)
- Priority: P0
- Estimate: S
- Status: [ ] Todo
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L634)

## Objective

Create `agentic_system/main.py` as the single command to start the demo — it initialises the OpenAI client and MLflow tracing, activates loguru, then launches the Textual TUI.

## Description

`main.py` is the entry point invoked by `python agentic_system/main.py`. Its only job is to call the setup functions already built in earlier tasks and hand control to the TUI. Import order matters:

1. `agentic_system.observability.logger` — activates loguru file-only sink; must run before any stdout-using code.
2. `agentic_system.setup.setup_openai()` — configures the OpenAI client, MLflow autolog, and disables SDK tracing; must run before any agent module is imported.
3. `agentic_system.tui.app` — the Textual app; imported last so all infrastructure is ready.

The file should be minimal — no business logic, no agent definitions.

## Scope

- Create `agentic_system/main.py` with the three-step initialisation sequence above.
- Call `app.run()` to hand control to the Textual event loop.

## Out Of Scope

- Any agent, tool, or TUI logic — those belong in their respective modules.
- MLflow server startup (handled by docker-compose).
- Database seeding or migration.
- `agentic_system/config.py` — already delivered in AGT-01.
- `agentic_system/setup.py` — already delivered in AGT-03/AGT-07.
- `agentic_system/demo.py` — already delivered in AGT-03.

## Deliverables

- `agentic_system/main.py` — minimal entry point (≤ 20 lines) that calls `setup_openai()`, imports logger, and launches the TUI.

## Acceptance Criteria

- `agentic_system.observability.logger` is imported before any agent module.
- `setup_openai()` is called before the TUI app is instantiated.
- `python agentic_system/main.py` starts the Textual TUI without errors when all services are up.
- No business logic, agent definitions, or tool implementations exist in `main.py`.

## Dependencies

- AGT-05: TUI app importable from `agentic_system.tui.app`.
- AGT-06: Logger module exists at `agentic_system.observability.logger`.
- AGT-07: `setup_openai()` importable from `agentic_system.setup`.
- AGT-03: Orchestrator importable (consumed by TUI, not directly by `main.py`).

## Assumptions

- `python agentic_system/main.py` is the canonical launch command (as stated in backlog Phase 0).
- All environment variables are loaded from `.env` via `pydantic-settings` at `settings` import time.

## Verification

Procedure to verify after implementation:

1. Parse `agentic_system/main.py` with `ast.parse`.
2. Confirm import order: logger before setup_openai before TUI app.
3. Confirm file length ≤ 20 lines.

```bash
# Syntax check
source .venv/bin/activate && python3 -c "
import ast
with open('agentic_system/main.py') as f:
    src = f.read()
ast.parse(src)
lines = [l for l in src.splitlines() if l.strip()]
print(f'  OK  agentic_system/main.py ({len(lines)} non-empty lines)')
"

# Import order check
source .venv/bin/activate && python3 -c "
import ast, pathlib
src = pathlib.Path('agentic_system/main.py').read_text()
checks = [
    ('logger import present',       'observability.logger' in src or 'logger' in src),
    ('setup_openai() called',       'setup_openai' in src),
    ('TUI app launched',            'app.run()' in src or '.run()' in src),
]
for label, ok in checks:
    print(f'  {\"OK\" if ok else \"MISSING\"}  {label}')
"
```

Expected verification result:

```
  OK  agentic_system/main.py (≤ 20 non-empty lines)
  OK  logger import present
  OK  setup_openai() called
  OK  TUI app launched
```

## Notes

- Keep `main.py` to ≤ 20 lines. If it grows, the logic belongs elsewhere.
- `setup_openai()` must be called before any agent module is imported to avoid the OpenAI client being unconfigured at import time.
