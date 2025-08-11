import asyncio
import uuid
from typing import assert_never

import asyncpg
from redis import Redis

from issue_solver.agents.agent_message_store import (
    AgentMessageStore,
    StreamingAgentMessageStore,
)
from issue_solver.agents.issue_resolving_agent import ResolveIssueCommand
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.app_settings import SolveCommandSettings, IssueSettings
from issue_solver.database.postgres_agent_message_store import PostgresAgentMessageStore
from issue_solver.git_operations.git_helper import GitHelper
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


async def init_agent_message_store(
    database_url: str | None, redis_url: str | None
) -> AgentMessageStore | None:
    if database_url and redis_url:
        agent_message_store = StreamingAgentMessageStore(
            PostgresAgentMessageStore(
                connection=await asyncpg.connect(
                    database_url.replace("+asyncpg", ""),
                    statement_cache_size=0,
                )
            ),
            redis_client=Redis.from_url(redis_url),
        )
        return agent_message_store
    return None


async def main(settings: SolveCommandSettings) -> None:
    issue_info = describe(settings.issue)
    agent_message_store = await init_agent_message_store(
        settings.database_url, settings.redis_url
    )
    agent = SupportedAgent.get(
        settings.agent,
        settings.model_settings,
        agent_messages=agent_message_store,
    )
    await agent.resolve_issue(
        ResolveIssueCommand(
            model=settings.versioned_ai_model,
            issue=issue_info,
            repo_path=settings.repo_path,
            process_id=settings.process_id or str(uuid.uuid4()),
        )
    )
    GitHelper.of(settings.git, settings.model_settings).commit_and_push(
        issue_info, settings.repo_path
    )


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
