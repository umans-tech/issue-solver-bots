import asyncio
import uuid
from typing import assert_never

from issue_solver.clock import UTCSystemClock
from issue_solver.events.domain import (
    IssueResolutionFailed,
    IssueResolutionStarted,
    IssueResolutionCompleted,
)
from issue_solver.cli.dependencies import init_command_dependencies
from issue_solver.agents.issue_resolving_agent import ResolveIssueCommand
from issue_solver.app_settings import SolveCommandSettings, IssueSettings
from issue_solver.issues.issue import IssueInfo
from issue_solver.issues.trackers.supported_issue_trackers import SupportedIssueTracker


class SolveCommand(SolveCommandSettings):
    def cli_cmd(self) -> None:
        print(
            f"[solve] 🧩 Solving issue='{self.issue}' with agent={self.agent} in repo={self.repo_path}"
        )
        asyncio.run(self.run_solve())

    async def run_solve(self) -> None:
        return await main(self)


async def main(settings: SolveCommandSettings) -> None:
    issue_info = describe(settings.issue)
    dependencies = await init_command_dependencies(settings)
    process_id = settings.process_id or str(uuid.uuid4())
    print(
        f"[solve] 🧩 Solving issue='{issue_info.title}' with agent={settings.agent} in repo={settings.repo_path} with process_id={process_id}"
    )

    try:
        await dependencies.event_store.append(
            process_id,
            IssueResolutionStarted(
                process_id=process_id,
                occurred_at=UTCSystemClock().now(),
            ),
        )
        await dependencies.coding_agent.resolve_issue(
            ResolveIssueCommand(
                model=settings.versioned_ai_model,
                issue=issue_info,
                repo_path=settings.repo_path,
                process_id=process_id,
            )
        )
        pr_reference = dependencies.git_client.commit_and_submit_pr(
            issue_info=issue_info,
            repo_path=settings.repo_path,
            git_repository_url=settings.git.repository_url,
            access_token=settings.git.access_token,
            process_id=process_id,
        )
        await dependencies.event_store.append(
            process_id,
            IssueResolutionCompleted(
                process_id=process_id,
                occurred_at=UTCSystemClock().now(),
                pr_number=pr_reference.number,
                pr_url=pr_reference.url,
            ),
        )
    except Exception as e:
        await dependencies.event_store.append(
            process_id,
            IssueResolutionFailed(
                reason="failed_resolving_issue",
                error_message=str(e),
                process_id=process_id,
                occurred_at=UTCSystemClock().now(),
            ),
        )
        raise e


def describe(issue: IssueInfo | IssueSettings) -> IssueInfo:
    match issue:
        case IssueSettings():
            issue_tracker = SupportedIssueTracker.get(issue.tracker)
            issue_info = issue_tracker.describe_issue(issue.ref)
        case IssueInfo():
            issue_info = issue
        case _:
            assert_never(issue)
    if issue_info is None:
        raise ValueError("Issue info could not be found. for issue: {issue}")
    return issue_info
