import asyncio
import uuid
from typing import assert_never

from issue_solver.clock import UTCSystemClock
from issue_solver.events.domain import IssueResolutionFailed, IssueResolutionCompleted
from issue_solver.standalone.dependencies import init_command_dependencies
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
        await dependencies.coding_agent.resolve_issue(
            ResolveIssueCommand(
                model=settings.versioned_ai_model,
                issue=issue_info,
                repo_path=settings.repo_path,
                process_id=process_id,
            )
        )
        dependencies.git_client.commit_and_push(
            issue_info=issue_info,
            repo_path=settings.repo_path,
            url=settings.git.access_token,
            access_token=settings.git.repository_url,
        )
        pr_reference = dependencies.git_client.submit_pull_request(
            repo_path=settings.repo_path,
            title=issue_info.title or f"automatic issue resolution {process_id}",
            body=issue_info.description,
            access_token=settings.git.access_token,
            url=settings.git.repository_url,
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
