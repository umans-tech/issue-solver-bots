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
