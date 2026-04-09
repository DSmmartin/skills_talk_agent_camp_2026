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

if settings.local_seed:
    _instructions += """

---

## LOCAL SEED OVERRIDE (active — local_seed=True)

The current dataset is the **18-row workshop fixture**. Only three repositories exist:
`org/repo-alpha`, `org/repo-beta`, and `org/repo-gamma`.

When retrieving schema context, always note:
- These are the only valid repo names for this session. Do not suggest `civicrm/civicrm-core` or any other repo.
- The schema is pre-migration: `merged UInt8` (1 = merged, 0 = not merged).
- There are no bot accounts — bot filters are unnecessary.
- Ghost contributors (no merged PRs): `ghost-user-1`, `ghost-user-2`, `ghost-user-3`, `ghost-user-4`.
- Regular contributors: `alice`, `bob`, `carol`, `dave`.
"""

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
