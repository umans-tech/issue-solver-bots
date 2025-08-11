import asyncio
import uuid
from typing import assert_never

import asyncpg

from issue_solver.clock import UTCSystemClock
from issue_solver.database.postgres_event_store import PostgresEventStore
from issue_solver.events.domain import IssueResolutionFailed, IssueResolutionCompleted
from issue_solver.events.event_store import InMemoryEventStore, EventStore
from issue_solver.streaming.streaming_agent_message_store import (
    init_agent_message_store,
)
from issue_solver.agents.issue_resolving_agent import ResolveIssueCommand
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.app_settings import SolveCommandSettings, IssueSettings
from issue_solver.git_operations.git_helper import GitClient
from issue_solver.issues.issue import IssueInfo
from issue_solver.issues.trackers.supported_issue_trackers import SupportedIssueTracker
from issue_solver.worker.messages_processing import Dependencies


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


async def init_command_dependencies(settings: SolveCommandSettings) -> Dependencies:
    database_url = settings.database_url
    agent_message_store = await init_agent_message_store(
        database_url, settings.redis_url
    )
    agent = SupportedAgent.get(
        settings.agent,
        settings.model_settings,
        agent_messages=agent_message_store,
    )
    git_client = GitClient()
    clock = UTCSystemClock()
    event_store = await init_event_store(database_url)
    return Dependencies(
        coding_agent=agent,
        git_client=git_client,
        clock=clock,
        event_store=event_store,
    )


async def init_event_store(database_url: str | None) -> EventStore:
    if database_url:
        return PostgresEventStore(
            connection=await asyncpg.connect(
                database_url.replace("+asyncpg", ""),
                statement_cache_size=0,
            )
        )
    return InMemoryEventStore()


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
