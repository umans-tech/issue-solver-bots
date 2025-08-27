import asyncpg
from redis import Redis

from issue_solver.agents.agent_message_store import (
    AgentMessageStore,
    InMemoryAgentMessageStore,
)
from issue_solver.cli.webhook_notifying_agent_message_store import (
    WebhookNotifyingAgentMessageStore,
)
from issue_solver.cli.webhook_notifying_event_store import WebhookNotifyingEventStore
from issue_solver.database.postgres_agent_message_store import PostgresAgentMessageStore
from issue_solver.database.postgres_event_store import PostgresEventStore
from issue_solver.events.event_store import EventStore, InMemoryEventStore
from issue_solver.queueing.sqs_events_publishing import SQSQueueingEventStore
from issue_solver.streaming.streaming_agent_message_store import (
    StreamingAgentMessageStore,
)


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


async def init_agent_message_store(
    database_url: str | None = None,
    redis_url: str | None = None,
    webhook_base_url: str | None = None,
) -> AgentMessageStore | None:
    agent_message_store = (
        PostgresAgentMessageStore(
            connection=await asyncpg.connect(
                database_url.replace("+asyncpg", ""),
                statement_cache_size=0,
            )
        )
        if database_url
        else InMemoryAgentMessageStore()
    )
    if redis_url and webhook_base_url:
        raise ValueError("Cannot provide both redis_url and webhook_base_url")
    if webhook_base_url:
        return WebhookNotifyingAgentMessageStore(
            agent_message_store,
            messages_webhook_url=f"{webhook_base_url.rstrip('/')}/webhooks/messages",
            http_client=None,
        )
    if redis_url:
        return StreamingAgentMessageStore(
            agent_message_store,
            redis_client=Redis.from_url(redis_url),
        )
    return agent_message_store
