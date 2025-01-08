import asyncio
from typing import assert_never

from issue_solver.agents.issue_resolving_agent import (
    IssueDescription,
    ResolveIssueCommand,
)
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.app_settings import AppSettings, IssueSettings
from issue_solver.git_operations.git_helper import GitHelper
from issue_solver.issues.trackers.issue_tracker import IssueInfo
from issue_solver.issues.supported_issue_trackers import SupportedIssueTracker


def to_issue_description(issue_info: IssueInfo | None) -> IssueDescription:
    if issue_info is None:
        raise ValueError("Issue info is required.")
    return IssueDescription(f"{issue_info.title}  \n {issue_info.description}")


async def main() -> None:
    settings = AppSettings()
    issue = settings.issue
    match issue:
        case IssueSettings():
            issue_tracker = SupportedIssueTracker.get(issue.tracker)
            issue_info = issue_tracker.describe_issue(issue.ref)
        case IssueInfo():
            issue_info = issue
        case _:
            assert_never(issue)
    issue_description = to_issue_description(issue_info)
    agent = SupportedAgent.get(settings.agent, settings.model_settings)
    await agent.resolve_issue(
        ResolveIssueCommand(
            model=settings.versioned_ai_model,
            issue_description=issue_description,
            repo_path=settings.repo_path,
        )
    )
    GitHelper.of(settings.git, settings.model_settings).commit_and_push(
        issue_description, settings.repo_path
    )


def run_main():
    asyncio.run(main())
