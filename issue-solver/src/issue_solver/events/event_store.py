from abc import abstractmethod, ABC
from typing import Any, TypeVar, Type
from issue_solver.events.domain import AnyDomainEvent

T = TypeVar("T", bound=AnyDomainEvent)


class EventStore(ABC):
    @abstractmethod
    async def append(self, process_id: str, event: AnyDomainEvent) -> None:
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

    async def append(self, process_id: str, event: AnyDomainEvent) -> None:
        if process_id not in self.events:
            self.events[process_id] = []
        self.events[process_id].append(event)

    async def get(self, process_id: str) -> list[AnyDomainEvent]:
        return self.events.get(process_id, [])
