from typing import Any, Type

import httpx

from issue_solver.events.domain import AnyDomainEvent, T
from issue_solver.events.event_store import EventStore
from issue_solver.events.serializable_records import serialize


class WebhookNotifyingEventStore(EventStore):
    def __init__(
        self, event_store: EventStore, event_webhook_url: str, http_client=httpx
    ):
        self.http_client = http_client
        self.event_store = event_store
        self.event_webhook_url = event_webhook_url

    async def append(self, process_id: str, *events: AnyDomainEvent) -> None:
        await self.event_store.append(process_id, *events)
        for event in events:
            self.http_client.post(
                url=self.event_webhook_url,
                json=serialize(event).model_dump(mode="json"),
            )

    async def get(self, process_id: str) -> list[AnyDomainEvent]:
        return await self.event_store.get(process_id)

    async def find(self, criteria: dict[str, Any], event_type: Type[T]) -> list[T]:
        return await self.event_store.find(criteria, event_type)
