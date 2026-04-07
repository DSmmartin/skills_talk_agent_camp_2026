"""
agentic_system/observability/logger.py

Configures loguru for file-only output so the Textual TUI owns the terminal.

Import this module as early as possible in main.py — before any other agent
module — so stdout suppression is in effect before any code runs.

Each process launch writes to its own timestamped file (logs/session_{time}.log),
giving per-session isolation without needing rotation.
"""

from pathlib import Path

from loguru import logger

# Remove the default loguru handler (stdout).
logger.remove()

# Ensure logs/ directory exists.
Path("logs").mkdir(exist_ok=True)

# One file per session, named by start time. DEBUG level captures all agent activity.
logger.add(
    "logs/session_{time}.log",
    level="DEBUG",
    format="{time} | {level} | {name} | {message}",
    enqueue=True,  # thread-safe async writes — safe with Textual's event loop
)
