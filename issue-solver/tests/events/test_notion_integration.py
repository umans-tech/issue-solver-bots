from datetime import timedelta, datetime

import pytest

from issue_solver.events.domain import NotionIntegrationFailed
from issue_solver.events.event_store import EventStore, InMemoryEventStore
from issue_solver.events.notion_integration import (
    get_notion_credentials,
    NotionCredentials,
)
from tests.examples.happy_path_persona import BriceDeNice


@pytest.fixture
def event_store() -> EventStore:
    return InMemoryEventStore()


@pytest.mark.asyncio
async def test_get_notion_credentials_when_missing(
    event_store: EventStore,
):
    # When
    credentials = await get_notion_credentials(event_store, BriceDeNice.team_space_id())

    # Then
    assert not credentials


@pytest.mark.asyncio
async def test_get_notion_credentials_when_just_connected(
    event_store: EventStore,
):
    # Given
    notion_integration_connected = BriceDeNice.connected_notion_workspace()
    await event_store.append(
        BriceDeNice.notion_integration_process_id(),
        notion_integration_connected,
    )

    # When
    credentials = await get_notion_credentials(event_store, BriceDeNice.team_space_id())

    # Then
    assert credentials == NotionCredentials.create_from(notion_integration_connected)


@pytest.mark.asyncio
async def test_get_notion_credentials_when_just_refreshed(
    event_store: EventStore,
):
    # Given
    notion_token_refreshed = BriceDeNice.rotated_notion_token()
    await event_store.append(
        BriceDeNice.notion_integration_process_id(),
        BriceDeNice.connected_notion_workspace(),
        notion_token_refreshed,
    )

    # When
    credentials = await get_notion_credentials(event_store, BriceDeNice.team_space_id())
    # Then
    assert credentials == NotionCredentials.create_from(notion_token_refreshed)


@pytest.mark.asyncio
async def test_get_notion_credentials_when_failed(
    event_store: EventStore,
):
    # Given
    notion_token_failed = NotionIntegrationFailed(
        error_type="invalid_token",
        occurred_at=datetime.fromisoformat("2025-01-01T12:05:00Z"),
        user_id="user-123",
        space_id=BriceDeNice.team_space_id(),
        process_id=BriceDeNice.notion_integration_process_id(),
        error_message="The token is invalid or has expired",
    )
    await event_store.append(
        BriceDeNice.notion_integration_process_id(),
        notion_token_failed,
    )

    # When
    credentials = await get_notion_credentials(event_store, BriceDeNice.team_space_id())

    # Then
    assert not credentials


@pytest.mark.asyncio
async def test_get_notion_credentials_when_failed_after_connected(
    event_store: EventStore,
):
    # Given
    notion_integration_connected = BriceDeNice.connected_notion_workspace()
    notion_token_failed = NotionIntegrationFailed(
        error_type="invalid_token",
        occurred_at=notion_integration_connected.occurred_at + timedelta(seconds=20),
        user_id=notion_integration_connected.user_id,
        space_id=notion_integration_connected.space_id,
        process_id=notion_integration_connected.process_id,
        error_message="The token is invalid or has expired",
    )
    await event_store.append(
        BriceDeNice.notion_integration_process_id(),
        notion_integration_connected,
        notion_token_failed,
    )

    # When
    credentials = await get_notion_credentials(event_store, BriceDeNice.team_space_id())

    # Then
    assert credentials == NotionCredentials.create_from(notion_integration_connected)
