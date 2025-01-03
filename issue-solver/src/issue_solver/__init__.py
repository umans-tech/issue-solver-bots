import asyncio

from issue_solver.agents.issue_resolving_agent import (
    IssueDescription,
    ResolveIssueCommand,
)
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.app_settings import AppSettings
from issue_solver.git_operations.git_helper import GitHelper
from issue_solver.issue_trackers import SupportedIssueTracker
from issue_solver.issue_trackers.issue_tracker import IssueInfo


def to_issue_description(issue_info: IssueInfo) -> IssueDescription:
    return IssueDescription(issue_info.title + " \n" + issue_info.description)


async def main() -> None:
    settings = AppSettings()
    issue_tracker = SupportedIssueTracker.get(settings.selected_issue_tracker)
    agent = SupportedAgent.get(settings.agent)
    issue_description = settings.issue_description or to_issue_description(
        issue_tracker.get_issue_description(settings.issue_id)
    )
    await agent.resolve_issue(
        ResolveIssueCommand(
            model=settings.agent_model,
            issue_description=issue_description,
            repo_path=settings.repo_path,
        )
    )
    GitHelper.of(settings.git_settings, settings.model_settings).commit_and_push(
        issue_description, settings.repo_path
    )


def run_main():
    asyncio.run(main())
