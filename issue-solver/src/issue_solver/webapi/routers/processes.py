import logging
from typing import Annotated, Self

from fastapi import APIRouter, Depends, HTTPException
from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    IssueResolutionRequested,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    IssueResolutionFailed,
)
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.events.serializable_records import (
    ProcessTimelineEventRecords,
    serialize,
)
from issue_solver.webapi.dependencies import get_event_store, get_logger
from pydantic import BaseModel

router = APIRouter(prefix="/processes", tags=["processes"])


class ProcessTimelineView(BaseModel):
    id: str
    type: str
    status: str
    events: list[ProcessTimelineEventRecords]

    @classmethod
    def create_from(cls, process_id: str, events: list[AnyDomainEvent]) -> Self:
        event_records = []
        for one_event in events:
            event_records.append(serialize(one_event).safe_copy())
        return cls(
            id=process_id,
            type=cls.infer_process_type(events),
            status=cls.to_status(events),
            events=event_records,
        )

    @classmethod
    def infer_process_type(cls, events: list[AnyDomainEvent]) -> str:
        if not events:
            raise ValueError("No events provided to infer process type.")
        first_event = events[0]
        if isinstance(first_event, IssueResolutionRequested):
            return "issue_resolution"
        return "code_repository_integration"

    @classmethod
    def to_status(cls, events: list[AnyDomainEvent]) -> str:
        events.sort(key=lambda event: event.occurred_at)
        last_event = events[-1]
        match last_event:
            case CodeRepositoryConnected():
                status = "connected"
            case CodeRepositoryIndexed():
                status = "indexed"
            case RepositoryIndexationRequested():
                status = "indexing"
            case IssueResolutionRequested():
                status = "requested"
            case IssueResolutionStarted():
                status = "in_progress"
            case IssueResolutionCompleted():
                status = "completed"
            case IssueResolutionFailed():
                status = "failed"
            case _:
                status = "unknown"
        return status


@router.get("/{process_id}")
async def get_process(
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
    process_events = await event_store.get(process_id)
    if not process_events:
        logger.warning(f"Process ID not found: {process_id}")
        raise HTTPException(status_code=404, detail="Process not found")
    process_timeline_view = ProcessTimelineView.create_from(process_id, process_events)
    logger.info(f"Found process with {len(process_events)} events")
    return process_timeline_view
