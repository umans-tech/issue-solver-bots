import logging
import os
from typing import assert_never

import asyncpg
from starlette.requests import Request

from issue_solver.agents.anthropic_agent import AnthropicAgent
from issue_solver.agents.coding_agent import CodingAgent
from issue_solver.agents.openai_agent import OpenAIAgent
from issue_solver.clock import Clock, UTCSystemClock
from issue_solver.database.postgres_event_store import PostgresEventStore
from issue_solver.events.event_store import EventStore
from issue_solver.git_operations.git_helper import (
    GitValidationService,
    DefaultGitValidationService,
    NoopGitValidationService,
)
from issue_solver.logging_config import default_logging_config
from issue_solver.webapi.payloads import ResolutionSettings

logger = default_logging_config.get_logger("issue_solver.webapi.dependencies")


def get_event_store(request: Request) -> EventStore:
    return request.app.state.event_store


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


def get_git_validation_service() -> GitValidationService:
    """
    Returns the Git validation service for the application.
    In production, this returns the DefaultGitValidationService.
    """
    return DefaultGitValidationService()


def get_noop_git_validation_service() -> GitValidationService:
    """
    Returns a no-op Git validation service for testing.
    This service doesn't perform actual validation and always succeeds.
    """
    return NoopGitValidationService()


def get_validation_service() -> GitValidationService:
    """
    Returns the appropriate Git validation service based on the environment.

    In testing environments (TESTING=true), returns the NoopGitValidationService.
    In production environments, returns the DefaultGitValidationService.
    """
    if os.environ.get("TESTING", "").lower() == "true":
        logger.debug("Using NoopGitValidationService for testing environment")
        return get_noop_git_validation_service()
    else:
        logger.debug("Using DefaultGitValidationService for production environment")
        return get_git_validation_service()


async def init_event_store() -> EventStore:
    return PostgresEventStore(
        connection=await asyncpg.connect(
            os.environ["DATABASE_URL"].replace("+asyncpg", ""), statement_cache_size=0
        )
    )
