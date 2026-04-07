"""
agent/orchestrator.py

Generic GitHub Archive query orchestrator using the AgentAsTools pattern.
The agent answers any question about GitHub contributor behaviour — it is not
scoped to ghost contributors. The demo question is defined separately in
agent/demo.py so this module stays reusable.
"""

from agents import Agent

from agentic_system.agents_core.rag.agent import rag_tool
from agentic_system.agents_core.nl2sql.agent import nl2sql_tool
from agentic_system.config import settings

_INSTRUCTIONS = """
You answer questions about GitHub contributor behaviour using the GitHub Archive
dataset stored in a ClickHouse database.

You have two tools:
- retrieve_schema_context: searches the vector database for field descriptions,
  type information, and SQL examples relevant to the question.
- query_github_data: translates a natural language question into ClickHouse SQL,
  executes it against the live database, and returns the rows and the SQL used.

Follow this workflow for every question:
1. Call retrieve_schema_context with the user question to get relevant schema context.
2. Call query_github_data passing BOTH the original question AND the full context
   returned in step 1. The SQL agent needs the context to generate correct queries.
3. Synthesise a clear, concise answer from the query results. Include the key numbers
   and a plain-language interpretation. Do not repeat raw SQL unless the user asks.

If the query returns zero rows, say so clearly — never fabricate data.
If you cannot answer confidently from the results, say so and explain why.
""".strip()

orchestrator = Agent(
    name="GithubDataOrchestrator",
    instructions=_INSTRUCTIONS,
    tools=[rag_tool, nl2sql_tool],
    model=settings.openai_model,
)
