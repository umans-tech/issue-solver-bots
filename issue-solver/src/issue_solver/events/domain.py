from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence, TypeVar


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


@dataclass(frozen=True, slots=True)
class CodeRepositoryConnectionFailed(DomainEvent):
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


AnyDomainEvent = (
    CodeRepositoryConnected
    | CodeRepositoryConnectionFailed
    | CodeRepositoryIndexed
    | RepositoryIndexationRequested
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
