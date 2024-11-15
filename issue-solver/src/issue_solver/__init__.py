import os
from typing import Callable

from issue_solver.agents import anthropic_tools
from issue_solver.start_resolution import (
    SolveIssueCommand,
    AgentModel,
    AgentName,
    IssueDescription,
)


async def main() -> None:
    print("Hello from issue-solver!")


def prepare_solve_issue(
        generate_patch: Callable[[SolveIssueCommand], None],
) -> Callable[[], None]:
    return lambda: generate_patch(
        SolveIssueCommand(
            agent_model=AgentModel(os.environ["AGENT_MODEL"]),
            agent_name=AgentName(os.environ["AGENT_NAME"]),
            issue_description=IssueDescription(os.environ["ISSUE_DESCRIPTION"]),
        )
    )
