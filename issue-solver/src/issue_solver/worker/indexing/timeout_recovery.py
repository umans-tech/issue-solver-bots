from datetime import datetime, timedelta
from typing import Iterable, Sequence

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    CodeRepositoryIntegrationFailed,
    RepositoryIndexationRequested,
)
from issue_solver.worker.dependencies import Dependencies


DEFAULT_TIMEOUT_THRESHOLD = timedelta(hours=2)


async def recover_timed_out_indexing(dependencies: Dependencies) -> None:
    event_store = dependencies.event_store
    now = dependencies.clock.now()

    stale_connections = await find_abandoned_indexing_processes(
        event_store, now, DEFAULT_TIMEOUT_THRESHOLD
    )

    await mark_indexing_as_timed_out(stale_connections, event_store, now)


async def find_abandoned_indexing_processes(
    event_store, now, threshold: timedelta
) -> list[CodeRepositoryConnected]:
    connections: Sequence[CodeRepositoryConnected] = await event_store.find(
        {}, CodeRepositoryConnected
    )
    stale: list[CodeRepositoryConnected] = []

    for connection in connections:
        events = await event_store.get(connection.process_id)
        if not events:
            continue

        last_event = events[-1]
        if isinstance(
            last_event, (CodeRepositoryIndexed, CodeRepositoryIntegrationFailed)
        ):
            continue

        latest_start = _latest_start_event_at(events)
        if not latest_start:
            continue

        if now - latest_start > threshold:
            stale.append(connection)

    return stale


async def mark_indexing_as_timed_out(
    connections: Iterable[CodeRepositoryConnected], event_store, occurred_at
) -> None:
    for connection in connections:
        failure_event = CodeRepositoryIntegrationFailed(
            url=connection.url,
            error_type="timeout",
            error_message="Indexing timed out during recovery sweep.",
            knowledge_base_id=connection.knowledge_base_id,
            process_id=connection.process_id,
            occurred_at=occurred_at,
        )
        await event_store.append(connection.process_id, failure_event)


def _latest_start_event_at(events) -> datetime | None:
    candidates = [
        e.occurred_at
        for e in events
        if isinstance(e, (CodeRepositoryConnected, RepositoryIndexationRequested))
    ]
    return max(candidates) if candidates else None
