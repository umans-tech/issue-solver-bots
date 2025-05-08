from datetime import datetime

import pytest

from tests.controllable_clock import ControllableClock
from issue_solver.events.event_store import EventStore, InMemoryEventStore

DEFAULT_CURRENT_TIME = datetime.fromisoformat("2022-01-01T00:00:00")


@pytest.fixture
def time_under_control() -> ControllableClock:
    return ControllableClock(DEFAULT_CURRENT_TIME)


@pytest.fixture
def event_store() -> EventStore:
    return InMemoryEventStore()
