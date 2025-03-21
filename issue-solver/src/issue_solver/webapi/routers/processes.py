import logging
from datetime import datetime
from typing import Annotated, Self, Literal

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from issue_solver.events.any_domain_event import AnyDomainEvent
from issue_solver.events.in_memory_event_store import InMemoryEventStore
from issue_solver.webapi.dependencies import get_event_store, get_logger

router = APIRouter(prefix="/processes", tags=["processes"])


class CodeRepositoryConnectedSchema(BaseModel):
    type: Literal["repository_connected"]
    occurred_at: datetime
    url: str
    access_token: str
    user_id: str
    space_id: str
    knowledge_base_id: str
    process_id: str


ProcessTimelineEventSchema = CodeRepositoryConnectedSchema


def obfuscate(secret: str) -> str:
    return "***********oken"


class ProcessTimelineView(BaseModel):
    id: str
    type: str
    status: str
    events: list[ProcessTimelineEventSchema]

    @classmethod
    def create_from(cls, process_id: str, events: list[AnyDomainEvent]) -> Self:
        event_records = []
        for event in events:
            event_records.append(
                CodeRepositoryConnectedSchema(
                    type="repository_connected",
                    occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
                    url=event.url,
                    access_token=obfuscate(event.access_token),
                    user_id=event.user_id,
                    space_id="Todo: get space id",
                    knowledge_base_id=event.knowledge_base_id,
                    process_id=event.process_id,
                )
            )
        return cls(
            id=process_id,
            type="code_repository_integration",
            status="connected",
            events=event_records,
        )


@router.get("/{process_id}")
def get_process(
    process_id: str,
    event_store: Annotated[InMemoryEventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger,
        Depends(
            lambda: get_logger("issue_solver.webapi.routers.processes.get_process")
        ),
    ],
) -> ProcessTimelineView:
    """Get information about a specific process."""
    logger.info(f"Retrieving information for process ID: {process_id}")
    process_events = event_store.get(process_id)
    if not process_events:
        logger.warning(f"Process ID not found: {process_id}")
        raise HTTPException(status_code=404, detail="Process not found")
    process_timeline_view = ProcessTimelineView.create_from(process_id, process_events)
    logger.info(f"Found process with {len(process_events)} events")
    return process_timeline_view
