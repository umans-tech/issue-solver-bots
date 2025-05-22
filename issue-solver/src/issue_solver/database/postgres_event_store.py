import json
import uuid
from typing import Any, Type

from issue_solver.events.domain import AnyDomainEvent, T
from issue_solver.events.event_store import EventStore
from issue_solver.events.serializable_records import (
    deserialize,
    get_record_type,
    serialize,
)


class PostgresEventStore(EventStore):
    def __init__(self, connection):
        self.connection = connection

    async def append(self, process_id: str, *events: AnyDomainEvent) -> None:
        for e in events:
            await self.append_one_event(process_id, e)

    async def append_one_event(self, process_id: str, event: AnyDomainEvent):
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
            INSERT INTO events_store (event_id,
                                      activity_id,
                                      position,
                                      event_type,
                                      data,
                                      metadata,
                                      occured_at)
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

    async def find(self, criteria: dict[str, Any], event_type: Type[T]) -> list[T]:
        sql_conditions = [
            f"data->>${i} = ${i + 1}" for i in range(1, len(criteria) * 2, 2)
        ]
        sql_conditions.append(f"event_type = ${len(criteria) * 2 + 1}")

        query = f"""
            SELECT event_type, data, metadata, occured_at
            FROM events_store
            WHERE {" AND ".join(sql_conditions)}
        """

        query_params = []
        for key, value in criteria.items():
            query_params.extend([key, value])
        event_record_type = get_record_type(event_type)
        query_params.append(event_record_type)

        rows = await self.connection.fetch(query, *query_params)
        events: list[T] = []

        for row in rows:
            db_event_type = row["event_type"]
            event = deserialize(db_event_type, row["data"])
            if not isinstance(event, event_type):
                raise ValueError(
                    f"Expected event type {event_record_type}, but got {db_event_type}"
                )
            events.append(event)

        return events
