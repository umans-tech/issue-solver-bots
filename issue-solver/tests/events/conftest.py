import pytest
from issue_solver.events.event_store import EventStore, InMemoryEventStore


@pytest.fixture
def event_store() -> EventStore:
    return InMemoryEventStore()
