from pathlib import Path

from agents import Agent

from agentic_system.agents_core.rag.tools.vector_search import vector_search
from agentic_system.config import settings

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_instructions = (
    (_PROMPTS_DIR / "system.md").read_text()
    + "\n\n"
    + (_PROMPTS_DIR / "examples.md").read_text()
)

agent_rag = Agent(
    name="AgentRAG",
    instructions=_instructions,
    tools=[vector_search],
    model=settings.openai_model,
)

rag_tool = agent_rag.as_tool(
    tool_name="retrieve_schema_context",
    tool_description=(
        "Retrieves schema field descriptions and SQL examples relevant to the question "
        "from the vector database. Call this first before generating any SQL."
    ),
)
