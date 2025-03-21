import logging
from typing import Annotated, Self

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from issue_solver.events.domain import AnyDomainEvent
from issue_solver.events.in_memory_event_store import InMemoryEventStore
from issue_solver.events.serializable_records import (
    CodeRepositoryConnectedRecord,
    ProcessTimelineEventRecords,
)
from issue_solver.webapi.dependencies import get_event_store, get_logger

router = APIRouter(prefix="/processes", tags=["processes"])


class ProcessTimelineView(BaseModel):
    id: str
    type: str
    status: str
    events: list[ProcessTimelineEventRecords]

    @classmethod
    def create_from(cls, process_id: str, events: list[AnyDomainEvent]) -> Self:
        event_records = []
        for event in events:
            event_records.append(
                CodeRepositoryConnectedRecord.create_from(event).safe_copy()
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
