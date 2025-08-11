import asyncpg

from issue_solver.database.postgres_event_store import PostgresEventStore
from issue_solver.events.event_store import EventStore, InMemoryEventStore


async def init_event_store(database_url: str | None) -> EventStore:
    if database_url:
        return PostgresEventStore(
            connection=await asyncpg.connect(
                database_url.replace("+asyncpg", ""),
                statement_cache_size=0,
            )
        )
    return InMemoryEventStore()
