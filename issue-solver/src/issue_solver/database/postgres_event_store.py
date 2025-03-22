import json
import uuid

from issue_solver.events.domain import AnyDomainEvent
from issue_solver.events.event_store import EventStore
from issue_solver.events.serializable_records import serialize, deserialize


class PostgresEventStore(EventStore):
    def __init__(self, connection):
        self.connection = connection

    async def append(self, process_id: str, event: AnyDomainEvent) -> None:
        next_position = await self.connection.fetchval(
            """
            SELECT COALESCE(MAX(position), 0) + 1
            FROM events_store
            WHERE activity_id = $1
            """,
            process_id,
        )

        record = serialize(event)
        event_id = str(uuid.uuid4())
        await self.connection.execute(
            """
            INSERT INTO events_store (
                event_id,
                activity_id,
                position,
                event_type,
                data,
                metadata,
                occured_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            event_id,
            process_id,
            next_position,
            record.type,
            record.model_dump_json(),
            json.dumps({}),
            record.occurred_at,
        )

    async def get(self, process_id: str) -> list[AnyDomainEvent]:
        rows = await self.connection.fetch(
            """
            SELECT event_type, data, metadata, occured_at
            FROM events_store
            WHERE activity_id = $1
            ORDER BY position ASC
            """,
            process_id,
        )

        events: list[AnyDomainEvent] = []
        for row in rows:
            event_type = row["event_type"]
            data = row["data"]
            domain_event = deserialize(event_type, data)
            events.append(domain_event)

        return events
