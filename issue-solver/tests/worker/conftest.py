from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from tests.controllable_clock import ControllableClock

from issue_solver.agents.issue_resolving_agent import (
    DocumentingAgent,
    IssueResolvingAgent,
)
from issue_solver.events.event_store import EventStore, InMemoryEventStore
from issue_solver.git_operations.git_helper import GitHelper
from issue_solver.worker.dependencies import Dependencies, IDGenerator
from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeRepository,
    KnowledgeBase,
)

DEFAULT_CURRENT_TIME = datetime.fromisoformat("2022-01-01T00:00:00")


@pytest.fixture
def time_under_control() -> ControllableClock:
    return ControllableClock(DEFAULT_CURRENT_TIME)


@pytest.fixture
def event_store() -> EventStore:
    return InMemoryEventStore()


class InMemoryKnowledgeRepository(KnowledgeRepository):
    def __init__(self):
        self._documents = {}

    def add(
        self,
        base: KnowledgeBase,
        document_name: str,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        if base not in self._documents:
            self._documents[base] = {}
        self._documents[base][document_name] = {
            "content": content,
            "metadata": metadata or {},
        }

    def contains(self, base: KnowledgeBase, document_name: str) -> bool:
        return document_name in self._documents.get(base, {})

    def get_content(self, base: KnowledgeBase, document_name: str) -> str:
        entry = self._documents.get(base, {}).get(document_name)
        if not entry:
            return ""
        return entry["content"]

    def list_entries(self, base: KnowledgeBase) -> list[str]:
        return list(self._documents.get(base, {}).keys())

    def get_metadata(self, base: KnowledgeBase, document_name: str) -> dict[str, str]:
        entry = self._documents.get(base, {}).get(document_name)
        if not entry:
            return {}
        return entry.get("metadata", {})


@pytest.fixture
def knowledge_repo() -> KnowledgeRepository:
    return InMemoryKnowledgeRepository()


@pytest.fixture
def id_generator() -> Mock:
    return Mock(spec=IDGenerator)


@pytest.fixture
def git_helper() -> Mock:
    return Mock(spec=GitHelper)


@pytest.fixture
def docs_agent() -> AsyncMock:
    return AsyncMock(spec=DocumentingAgent)


@pytest.fixture
def coding_agent() -> AsyncMock:
    return AsyncMock(spec=IssueResolvingAgent)


@pytest.fixture
def worker_dependencies(
    coding_agent: AsyncMock,
    docs_agent: AsyncMock,
    event_store: EventStore,
    git_helper: Mock,
    id_generator: Mock,
    knowledge_repo: KnowledgeRepository,
    time_under_control,
) -> Dependencies:
    dependencies = Dependencies(
        event_store,
        git_helper,
        coding_agent,
        knowledge_repo,
        time_under_control,
        id_generator=id_generator,
        docs_agent=docs_agent,
    )
    return dependencies
