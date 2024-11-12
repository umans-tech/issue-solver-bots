import os
from typing import Callable

from issue_solver.agents import claude_tools
from issue_solver.start_resolution import (
    SolveIssueCommand,
    AgentModel,
    AgentName,
    IssueDescription,
)
from issue_solver.agents.claude_tools.setup import start_resolution as start_claude_tools_resolution


def main() -> None:
    print("Hello from issue-solver!")
    start_claude_tools_resolution()


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
