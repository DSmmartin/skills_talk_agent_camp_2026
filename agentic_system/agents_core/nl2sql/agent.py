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

if settings.local_seed:
    _instructions += """

---

## LOCAL SEED OVERRIDE (active — local_seed=True)

The dataset currently loaded is the **18-row local fixture**, not the 5M-row GitHub Archive sample.
Disregard the dataset facts section above entirely. Use the following instead:

- **Total rows:** 18
- **Repos in the dataset:** `org/repo-alpha`, `org/repo-beta`, `org/repo-gamma` — these are the ONLY repos present.
- **Date range:** 2024-01-10 → 2024-03-01
- **Ghost contributors** (zero merged PRs): `ghost-user-1` (org/repo-alpha), `ghost-user-2` and `ghost-user-3` (org/repo-beta), `ghost-user-4` (org/repo-gamma)
- **Regular contributors** (at least one merged PR): `alice` and `bob` (org/repo-alpha), `carol` (org/repo-beta), `dave` (org/repo-gamma)

Rules that change in local mode:
- Do NOT pivot to `civicrm/civicrm-core` or any other repo. `org/repo-alpha`, `org/repo-beta`, and `org/repo-gamma` are valid and fully populated.
- Do NOT add bot filters — there are no bot accounts in this dataset.
- The schema is still pre-migration: `merged UInt8` (1 = merged, 0 = not merged). All other SQL rules apply unchanged.
- When the user asks about ghost contributors without specifying a repo, query all three repos.
"""

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
