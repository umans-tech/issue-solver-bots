from unittest.mock import Mock

import pytest
from tests.examples.happy_path_persona import examples_of_all_events

from issue_solver.cli.webhook_notifying_event_store import WebhookNotifyingEventStore
from issue_solver.events.domain import AnyDomainEvent
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.factories import init_event_store
from issue_solver.queueing.sqs_events_publishing import SQSQueueingEventStore


@pytest.mark.parametrize(
    "event_type,event",
    examples_of_all_events(),
)
@pytest.mark.asyncio
async def test_webhook_notifying_eventstore(event_type: str, event: AnyDomainEvent):
    # Given
    http_client_mock = Mock()
    http_client_mock.post.return_value.status_code = 200
    event_store = WebhookNotifyingEventStore(
        event_store=InMemoryEventStore(),
        event_webhook_url="https://api.example.umans.ai/webhooks/events",
        http_client=http_client_mock,
    )

    # When
    await event_store.append(event.process_id, event)

    # Then
    http_client_mock.post.assert_called_once()
    retrieved_events = await event_store.get(event.process_id)
    assert retrieved_events == [event]


@pytest.mark.asyncio
async def test_init_event_store_should_return_webhook_notifying_event_store_when_event_webhook_url_provided():
    # When
    event_store = await init_event_store(
        webhook_base_url="https://api.example.umans.ai"
    )

    # Then
    assert isinstance(event_store, WebhookNotifyingEventStore)
    assert (
        event_store.event_webhook_url == "https://api.example.umans.ai/webhooks/events"
    )


@pytest.mark.asyncio
async def test_init_event_store_should_tolerate_trailing_slash_in_event_webhook_url():
    # When
    event_store = await init_event_store(
        webhook_base_url="https://api.example.umans.ai/"
    )

    # Then
    assert isinstance(event_store, WebhookNotifyingEventStore)
    assert (
        event_store.event_webhook_url == "https://api.example.umans.ai/webhooks/events"
    )


@pytest.mark.asyncio
async def test_init_event_store_should_return_sqs_queueing_event_store_when_queue_url_provided():
    # When
    event_store = await init_event_store(
        queue_url="http://sqs.eu-west-3.testqueue.localhost.localstack.cloud:4566/000000000000/process-queue"
    )

    # Then
    assert isinstance(event_store, SQSQueueingEventStore)


@pytest.mark.asyncio
async def test_init_event_store_should_raise_exception_when_both_queue_url_and_event_webhook_url_provided():
    # When / Then
    with pytest.raises(ValueError):
        await init_event_store(
            queue_url="http://sqs.eu-west-3.testqueue.localhost.localstack.cloud:4566/000000000000/process-queue",
            webhook_base_url="https://api.example.umans.ai",
        )
