import logging
import os
from typing import assert_never

import asyncpg
from fastapi import Header
from redis import Redis

from issue_solver.agents.agent_message_store import (
    AgentMessageStore,
)
from issue_solver.streaming.streaming_agent_message_store import (
    StreamingAgentMessageStore,
)
from issue_solver.agents.anthropic_agent import AnthropicAgent
from issue_solver.agents.coding_agent import CodingAgent
from issue_solver.agents.openai_agent import OpenAIAgent
from issue_solver.clock import Clock, UTCSystemClock
from issue_solver.database.postgres_agent_message_store import PostgresAgentMessageStore
from issue_solver.database.postgres_event_store import PostgresEventStore
from issue_solver.events.event_store import EventStore
from issue_solver.git_operations.git_helper import (
    DefaultGitValidationService,
    GitValidationService,
)
from issue_solver.logging_config import default_logging_config
from issue_solver.webapi.payloads import ResolutionSettings
from starlette.requests import Request

logger = default_logging_config.get_logger("issue_solver.webapi.dependencies")


def get_event_store(request: Request) -> EventStore:
    return request.app.state.event_store


def get_agent_message_store(request: Request) -> AgentMessageStore:
    return request.app.state.agent_message_store


def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis_client


async def get_user_id_or_default(
    x_user_id: str = Header(None, alias="X-User-ID"),
) -> str:
    return x_user_id or "unknown"


def get_agent(setting: ResolutionSettings) -> CodingAgent:
    match setting.agent:
        case "openai-tools":
            return OpenAIAgent(api_key=os.environ["OPENAI_API_KEY"])
        case "anthropic-tools":
            return AnthropicAgent(
                api_key=os.environ["ANTHROPIC_API_KEY"],
            )
        case _:
            assert_never(setting.agent)


def get_logger(
    name: str, level: int | None = None
) -> logging.Logger | logging.LoggerAdapter:
    return default_logging_config.get_logger(name, level)


def get_clock() -> Clock:
    return UTCSystemClock()


def get_validation_service() -> GitValidationService:
    return DefaultGitValidationService()


async def init_event_store() -> EventStore:
    return PostgresEventStore(
        connection=await asyncpg.connect(
            os.environ["DATABASE_URL"].replace("+asyncpg", ""), statement_cache_size=0
        )
    )


async def init_agent_message_store() -> AgentMessageStore:
    agent_message_store = StreamingAgentMessageStore(
        PostgresAgentMessageStore(
            connection=await asyncpg.connect(
                os.environ["DATABASE_URL"].replace("+asyncpg", ""),
                statement_cache_size=0,
            )
        ),
        redis_client=Redis.from_url(os.environ["REDIS_URL"]),
    )
    return agent_message_store
