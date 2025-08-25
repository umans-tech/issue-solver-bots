import asyncpg

from issue_solver.database.postgres_event_store import PostgresEventStore
from issue_solver.events.event_store import EventStore, InMemoryEventStore
from issue_solver.queueing.sqs_events_publishing import SQSQueueingEventStore
from issue_solver.cli.webhook_notifying_event_store import WebhookNotifyingEventStore


async def init_event_store(
    database_url: str | None = None,
    queue_url: str | None = None,
    event_webhook_url: str | None = None,
) -> EventStore:
    if queue_url and event_webhook_url:
        raise ValueError("Cannot provide both queue_url and event_webhook_url")
    event_store = (
        await persistent_event_store(database_url)
        if database_url
        else InMemoryEventStore()
    )
    return (
        SQSQueueingEventStore(event_store, queue_url=queue_url)
        if queue_url
        else WebhookNotifyingEventStore(
            event_store, event_webhook_url=event_webhook_url
        )
        if event_webhook_url
        else event_store
    )


async def persistent_event_store(database_url: str) -> EventStore:
    return PostgresEventStore(
        connection=await asyncpg.connect(
            database_url,
            statement_cache_size=0,
        )
    )
