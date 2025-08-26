import asyncpg

from issue_solver.cli.webhook_notifying_event_store import WebhookNotifyingEventStore
from issue_solver.database.postgres_event_store import PostgresEventStore
from issue_solver.events.event_store import EventStore, InMemoryEventStore
from issue_solver.queueing.sqs_events_publishing import SQSQueueingEventStore


async def init_event_store(
    database_url: str | None = None,
    queue_url: str | None = None,
    webhook_base_url: str | None = None,
) -> EventStore:
    if queue_url and webhook_base_url:
        raise ValueError("Cannot provide both queue_url and webhook_base_url")
    event_store = (
        await persistent_event_store(database_url)
        if database_url
        else InMemoryEventStore()
    )
    return (
        SQSQueueingEventStore(event_store, queue_url=queue_url)
        if queue_url
        else WebhookNotifyingEventStore(
            event_store, event_webhook_url=get_event_webhook_url(webhook_base_url)
        )
        if webhook_base_url
        else event_store
    )


async def persistent_event_store(database_url: str) -> EventStore:
    return PostgresEventStore(
        connection=await asyncpg.connect(
            database_url,
            statement_cache_size=0,
        )
    )


def get_event_webhook_url(webhook_base_url: str) -> str:
    return f"{webhook_base_url.rstrip('/')}/webhooks/events"
