from datetime import datetime

import pytest

from tests.controllable_clock import ControllableClock
from issue_solver.events.event_store import EventStore, InMemoryEventStore
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

    def add(self, base: KnowledgeBase, document_name: str, content: str) -> None:
        if base not in self._documents:
            self._documents[base] = {}
        self._documents[base][document_name] = content

    def contains(self, base: KnowledgeBase, document_name: str) -> bool:
        return document_name in self._documents.get(base, {})

    def get_content(self, base: KnowledgeBase, document_name: str) -> str:
        return self._documents.get(base, {}).get(document_name, "")

    def list_entries(self, base: KnowledgeBase) -> list[str]:
        return list(self._documents.get(base, {}).keys())


@pytest.fixture
def knowledge_repo() -> KnowledgeRepository:
    return InMemoryKnowledgeRepository()
