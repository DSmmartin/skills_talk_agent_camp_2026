from pathlib import Path

from agents import Agent

from agentic_system.agents_core.nl2sql.tools.run_sql import run_sql
from agentic_system.config import settings

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_instructions = (
    (_PROMPTS_DIR / "system.md").read_text()
    + "\n\n"
    + (_PROMPTS_DIR / "examples.md").read_text()
)

agent_nl2sql = Agent(
    name="AgentNL2SQL",
    instructions=_instructions,
    tools=[run_sql],
    model=settings.openai_model,
)

nl2sql_tool = agent_nl2sql.as_tool(
    tool_name="query_github_data",
    tool_description=(
        "Translates a natural language question about GitHub contributors into ClickHouse SQL, "
        "executes it, and returns the results. "
        "Pass the schema context from retrieve_schema_context along with the question. "
        "Unmerged PRs use merged = 0; merged PRs use merged = 1."
    ),
)
