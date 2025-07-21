from typing import Sequence

from issue_solver.events.domain import (
    DomainEvent,
    most_recent_event,
    CodeRepositoryTokenRotated,
    CodeRepositoryConnected,
)
from issue_solver.events.event_store import EventStore


async def get_access_token(event_store: EventStore, process_id: str) -> str | None:
    events = await event_store.get(process_id)
    return get_most_recent_access_token(events)


def get_most_recent_access_token(
    domain_events: Sequence[DomainEvent],
) -> str | None:
    token_rotated = most_recent_event(domain_events, CodeRepositoryTokenRotated)
    connected = most_recent_event(domain_events, CodeRepositoryConnected)

    if token_rotated and connected:
        return (
            max(token_rotated.occurred_at, connected.occurred_at)
            == token_rotated.occurred_at
            and token_rotated.new_access_token
            or connected.access_token
        )

    if token_rotated:
        return token_rotated.new_access_token

    if connected:
        return connected.access_token

    return None


def get_most_recent_token_permissions(
    domain_events: Sequence[DomainEvent],
) -> dict | None:
    """Get the most recent token permissions from either connected or token rotated events."""
    token_rotated = most_recent_event(domain_events, CodeRepositoryTokenRotated)
    connected = most_recent_event(domain_events, CodeRepositoryConnected)

    if token_rotated and connected:
        # Return permissions from the most recent event
        if (
            max(token_rotated.occurred_at, connected.occurred_at)
            == token_rotated.occurred_at
        ):
            return token_rotated.token_permissions
        else:
            return connected.token_permissions

    if token_rotated:
        return token_rotated.token_permissions

    if connected:
        return connected.token_permissions

    return None


async def get_connected_repo_event(
    event_store, space_id
) -> CodeRepositoryConnected | None:
    connected_repo_event = None
    if space_id:
        # Find any repository connected to this space, regardless of which user connected it
        events = await event_store.find({"space_id": space_id}, CodeRepositoryConnected)
        connected_repo_event = most_recent_event(events, CodeRepositoryConnected)
    return connected_repo_event
