import asyncio

from issue_solver.agents.issue_resolving_agent import (
    IssueDescription,
    ResolveIssueCommand,
)
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.app_settings import AppSettings
from issue_solver.git_operations.git_helper import GitHelper
from issue_solver.issue_trackers.issue_tracker import IssueInfo
from issue_solver.issue_trackers.supported_issue_trackers import SupportedIssueTracker


def to_issue_description(issue_info: IssueInfo | None) -> IssueDescription:
    if issue_info is None:
        raise ValueError("Issue info is required.")
    return IssueDescription(f"{issue_info.title}  \n {issue_info.description}")


async def main() -> None:
    settings = AppSettings()
    issue_tracker = SupportedIssueTracker.get(settings.selected_issue_tracker)
    agent = SupportedAgent.get(settings.agent)
    issue_description = settings.issue_description or to_issue_description(
        issue_tracker.describe_issue(settings.issue_id)
    )
    await agent.resolve_issue(
        ResolveIssueCommand(
            model=settings.model_name,
            issue_description=issue_description,
            repo_path=settings.repo_path,
        )
    )
    GitHelper.of(settings.git_settings, settings.model_settings).commit_and_push(
        issue_description, settings.repo_path
    )


def run_main():
    asyncio.run(main())
