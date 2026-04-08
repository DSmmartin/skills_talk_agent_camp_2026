# 03 — Fully Guided Skill

The complete procedure. Exact commands, validated tooling, full replacement list, rollback.

## What it adds over 02_agent_assisted

- One-command fix (`schema_sync.py`) for the standard migration case
- Step-by-step fallback procedure for non-standard migrations
- Exact `uv run` commands for each script
- `references/schema-layers.md` — full replacement list per layer, embedding algorithm, connection settings
- Pre-check and post-check validation steps
- Rollback procedure with exact commands

## The key property

Claude follows the skill reliably every time. No exploration, no guessing. If the migration matches the procedure (it does in this demo), it is resolved in one command.

## Balance point

| Dimension | 00_naive | 03_fully_guided |
|-----------|----------|-----------------|
| Claude effort | High | Low |
| Token cost | High | Low |
| Reliability | Unpredictable | Consistent |
| Generality | Any problem | This migration pattern |
| Maintenance | None | Update when pattern changes |

The sweet spot is `03_fully_guided`: specific enough to be reliable and cheap, general enough to handle the standard migration scenario in this system.
