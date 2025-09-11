from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence, TypeVar

from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.env_setup.dev_environments_management import (
    ExecutionEnvironmentPreference,
)
from issue_solver.issues.issue import IssueInfo
from issue_solver.models.supported_models import (
    SupportedAIModel,
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_VERSION,
)


@dataclass(kw_only=True, frozen=True)
class DomainEvent(ABC):
    @property
    @abstractmethod
    def occurred_at(self) -> datetime:
        pass

    @property
    @abstractmethod
    def process_id(self) -> str:
        pass


@dataclass(frozen=True, slots=True)
class CodeRepositoryConnected(DomainEvent):
    url: str
    access_token: str
    user_id: str
    space_id: str
    knowledge_base_id: str
    process_id: str
    occurred_at: datetime
    token_permissions: dict | None = None


@dataclass(frozen=True, slots=True)
class CodeRepositoryTokenRotated(DomainEvent):
    knowledge_base_id: str
    new_access_token: str
    user_id: str
    process_id: str
    occurred_at: datetime
    token_permissions: dict | None = None


@dataclass(frozen=True, slots=True)
class CodeRepositoryIntegrationFailed(DomainEvent):
    url: str
    error_type: str
    error_message: str
    knowledge_base_id: str
    process_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class CodeRepositoryIndexed(DomainEvent):
    branch: str
    commit_sha: str
    stats: dict[str, Any]
    knowledge_base_id: str
    process_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class RepositoryIndexationRequested(DomainEvent):
    knowledge_base_id: str
    user_id: str
    process_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class IssueResolutionRequested(DomainEvent):
    knowledge_base_id: str
    issue: IssueInfo
    process_id: str
    occurred_at: datetime
    user_id: str = "unknown-user-id"  # Default value for retro-compatibility. This can be removed in the future if not needed anymore.
    agent: SupportedAgent = SupportedAgent.CLAUDE_CODE
    max_turns: int = 100
    ai_model: SupportedAIModel = SupportedAnthropicModel.CLAUDE_SONNET_4
    ai_model_version: str | None = LATEST_CLAUDE_4_VERSION
    execution_environment: ExecutionEnvironmentPreference = (
        ExecutionEnvironmentPreference.ENV_PREFERRED
    )

    def needs_environment(self) -> bool:
        return (
            self.execution_environment != ExecutionEnvironmentPreference.NO_ENV_REQUIRED
        )


@dataclass(frozen=True, slots=True)
class IssueResolutionStarted(DomainEvent):
    process_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class IssueResolutionCompleted(DomainEvent):
    pr_url: str
    pr_number: int
    process_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class IssueResolutionFailed(DomainEvent):
    reason: str
    error_message: str
    process_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class EnvironmentConfigurationProvided(DomainEvent):
    environment_id: str
    knowledge_base_id: str
    project_setup: str
    user_id: str
    process_id: str
    occurred_at: datetime
    global_setup: str | None = None


@dataclass(frozen=True, slots=True)
class IssueResolutionEnvironmentPrepared(DomainEvent):
    environment_id: str
    instance_id: str
    knowledge_base_id: str
    process_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class EnvironmentConfigurationValidated(DomainEvent):
    snapshot_id: str
    stdout: str
    stderr: str
    return_code: int
    process_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class EnvironmentValidationFailed(DomainEvent):
    stdout: str
    stderr: str
    return_code: int
    process_id: str
    occurred_at: datetime


AnyDomainEvent = (
    CodeRepositoryConnected
    | CodeRepositoryTokenRotated
    | CodeRepositoryIntegrationFailed
    | CodeRepositoryIndexed
    | RepositoryIndexationRequested
    | IssueResolutionRequested
    | IssueResolutionStarted
    | IssueResolutionCompleted
    | IssueResolutionFailed
    | EnvironmentConfigurationProvided
    | IssueResolutionEnvironmentPrepared
    | EnvironmentConfigurationValidated
    | EnvironmentValidationFailed
)


T = TypeVar("T", bound=AnyDomainEvent)


def most_recent_event(
    domain_events: Sequence[DomainEvent], event_to_find: type[T]
) -> T | None:
    events_of_type = all_events_of_type(domain_events, event_to_find)
    if not events_of_type:
        return None
    return max(events_of_type, key=lambda e: e.occurred_at)


def first_event_of_type(
    domain_events: Sequence[DomainEvent], event_to_find: type[T]
) -> T | None:
    for event in domain_events:
        if isinstance(event, event_to_find):
            return event
    return None


def all_events_of_type(
    domain_events: Sequence[DomainEvent], event_to_find: type[T]
) -> list[T]:
    events_to_find: list[T] = []

    for event in domain_events:
        if isinstance(event, event_to_find):
            events_to_find.append(event)

    return events_to_find
