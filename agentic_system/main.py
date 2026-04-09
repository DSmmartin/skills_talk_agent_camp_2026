"""
agentic_system/main.py

Entry point for the Ghost Contributors app.

Import order is deliberate:
  1. observability.logger  — removes stdout before any agent code runs
  2. setup.setup_openai()  — configures OpenAI client + MLflow before agents import
  3. tui.app               — Textual app; imported last so all infra is ready
"""

import agentic_system.observability.logger  # noqa: F401 — side-effect: removes stdout

from loguru import logger

from agentic_system.setup import setup_openai
from agentic_system.tui.app import GhostContributorsApp

setup_openai()
logger.info("TUI startup: Ghost Contributors app")

if __name__ == "__main__":
    GhostContributorsApp().run()
