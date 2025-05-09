from abc import abstractmethod, ABC
from typing import Any, Type
from issue_solver.events.domain import AnyDomainEvent, T


class EventStore(ABC):
    @abstractmethod
    async def append(self, process_id: str, *events: AnyDomainEvent) -> None:
        pass

    @abstractmethod
    async def get(self, process_id: str) -> list[AnyDomainEvent]:
        pass

    @abstractmethod
    async def find(self, criteria: dict[str, Any], event_type: Type[T]) -> list[T]:
        pass


class InMemoryEventStore(EventStore):
    def __init__(self):
        self.events = {}

    async def append(self, process_id: str, *events: AnyDomainEvent) -> None:
        if process_id not in self.events:
            self.events[process_id] = []
        for e in events:
            self.events[process_id].append(e)

    async def get(self, process_id: str) -> list[AnyDomainEvent]:
        return self.events.get(process_id, [])

    async def find(self, criteria: dict[str, Any], event_type: Type[T]) -> list[T]:
        result = []
        for process_id, events in self.events.items():
            for event in events:
                if isinstance(event, event_type):
                    match = all(
                        getattr(event, key) == value for key, value in criteria.items()
                    )
                    if match:
                        result.append(event)
        return result
