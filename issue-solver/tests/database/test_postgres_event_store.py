from datetime import datetime

import pytest

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
)
from issue_solver.events.event_store import EventStore


@pytest.mark.asyncio
async def test_find_should_return_events_with_matching_criteria(
    event_store: EventStore,
):
    # Given
    appended_event = CodeRepositoryConnected(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        url="https://github.com/test/repo",
        access_token="s3c3t-3t0k3n",
        user_id="test-user-id",
        space_id="test-space-id",
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    found_events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
            "user_id": "test-user-id",
        },
        event_type=CodeRepositoryConnected,
    )

    # Then
    assert found_events == [appended_event]


@pytest.mark.asyncio
async def test_find_should_return_empty_list_when_no_events_match_criteria(
    event_store: EventStore,
):
    # Given
    appended_event = CodeRepositoryConnected(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        url="https://github.com/test/repo",
        access_token="s3c3t-3t0k3n",
        user_id="test-user-id",
        space_id="test-space-id",
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    found_events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
            "user_id": "unknown-user-id",
        },
        event_type=CodeRepositoryConnected,
    )

    # Then
    assert not found_events


@pytest.mark.asyncio
async def test_find_should_return_empty_list_when_event_type_does_not_match(
    event_store: EventStore,
):
    # Given
    appended_event = CodeRepositoryConnected(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        url="https://github.com/test/repo",
        access_token="s3c3t-3t0k3n",
        user_id="test-user-id",
        space_id="test-space-id",
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    found_events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
        },
        event_type=CodeRepositoryIndexed,
    )

    # Then
    assert not found_events


@pytest.mark.asyncio
async def test_get_event_repository_indexation_requested(event_store: EventStore):
    # Given
    appended_event = RepositoryIndexationRequested(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
        user_id="test-user-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    events = await event_store.get("test-process-id")

    # Then
    assert events == [appended_event]


@pytest.mark.asyncio
async def test_find_event_repository_indexation_requested(event_store: EventStore):
    # Given
    appended_event = RepositoryIndexationRequested(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
        user_id="test-user-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
        },
        event_type=RepositoryIndexationRequested,
    )

    # Then
    assert events == [appended_event]
