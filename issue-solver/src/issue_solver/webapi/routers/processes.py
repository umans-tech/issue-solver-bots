import json
import logging
from dataclasses import asdict
from typing import Annotated, Self, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import StreamingResponse

from issue_solver.agents.agent_message_store import AgentMessageStore, AgentMessage
from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryTokenRotated,
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
from issue_solver.webapi.dependencies import (
    get_event_store,
    get_logger,
    get_agent_message_store,
)
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
        status_affecting_events = [
            event
            for event in events
            if not isinstance(event, CodeRepositoryTokenRotated)
        ]

        if not status_affecting_events:
            return "unknown"

        status_affecting_events.sort(key=lambda event: event.occurred_at)
        last_event = status_affecting_events[-1]
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


@router.get("/")
async def list_processes(
    event_store: Annotated[InMemoryEventStore, Depends(get_event_store)],
    space_id: str | None = Query(None, description="Filter by space ID"),
    knowledge_base_id: str | None = Query(
        None, description="Filter by knowledge base ID"
    ),
    process_type: str | None = Query(None, description="Filter by process type"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of processes to return"),
    offset: int = Query(0, ge=0, description="Number of processes to skip"),
) -> dict:
    """List processes with filtering and pagination."""

    # Determine which processes to get based on filters
    if space_id or knowledge_base_id:
        processes = await _get_processes_by_criteria(
            event_store, space_id, knowledge_base_id
        )
    else:
        # If filtering by type or status only, get all processes
        processes = await _get_all_processes(event_store)

    # Apply additional filters
    filtered_processes = _apply_filters(processes, process_type, status)

    # Apply pagination
    total = len(filtered_processes)
    paginated_processes = filtered_processes[offset : offset + limit]

    return {
        "processes": paginated_processes,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def _get_processes_by_criteria(
    event_store: InMemoryEventStore, space_id: str | None, knowledge_base_id: str | None
) -> list[dict]:
    """Get processes based on space_id or knowledge_base_id criteria."""
    processes = []

    if space_id:
        repo_events = await event_store.find(
            criteria={"space_id": space_id}, event_type=CodeRepositoryConnected
        )
        processes.extend(await _convert_events_to_processes(event_store, repo_events))

    if knowledge_base_id:
        repo_events = await event_store.find(
            criteria={"knowledge_base_id": knowledge_base_id},
            event_type=CodeRepositoryConnected,
        )
        processes.extend(await _convert_events_to_processes(event_store, repo_events))

        issue_events = await event_store.find(
            criteria={"knowledge_base_id": knowledge_base_id},
            event_type=IssueResolutionRequested,
        )
        processes.extend(await _convert_events_to_processes(event_store, issue_events))

    return processes


def _apply_filters(
    processes: list[dict], process_type: str | None, status: str | None
) -> list[dict]:
    """Apply type and status filters to processes."""
    filtered = processes

    if process_type:
        filtered = [p for p in filtered if p["type"] == process_type]

    if status:
        filtered = [p for p in filtered if p["status"] == status]

    return filtered


async def _get_all_processes(event_store: InMemoryEventStore) -> list[dict]:
    """Get all processes from all event types."""
    all_processes = []

    # Get all repository processes
    repo_events = await event_store.find(
        criteria={}, event_type=CodeRepositoryConnected
    )
    all_processes.extend(await _convert_events_to_processes(event_store, repo_events))

    # Get all issue resolution processes
    issue_events = await event_store.find(
        criteria={}, event_type=IssueResolutionRequested
    )
    all_processes.extend(await _convert_events_to_processes(event_store, issue_events))

    return all_processes


async def _convert_events_to_processes(
    event_store: InMemoryEventStore, events: list
) -> list[dict]:
    """Convert domain events to process timeline views."""
    processes = []
    for event in events:
        process_events = await event_store.get(event.process_id)
        process_view = ProcessTimelineView.create_from(event.process_id, process_events)
        processes.append(process_view.model_dump())
    return processes


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


@router.get(
    "/{process_id}/messages",
)
async def get_process_messages(
    process_id: str,
    agent_message_store: Annotated[AgentMessageStore, Depends(get_agent_message_store)],
) -> list[AgentMessage]:
    """Get existing messages for a specific process."""

    historical_messages = await agent_message_store.get(
        process_id=process_id,
    )
    return historical_messages


@router.get(
    "/{process_id}/messages/stream",
)
async def stream_process_messages(
    process_id: str,
    agent_message_store: Annotated[AgentMessageStore, Depends(get_agent_message_store)],
) -> StreamingResponse:
    """Stream messages for a specific process.
    This endpoint returns a stream of messages in newline-delimited JSON format."""

    async def message_generator() -> AsyncGenerator[str, None]:
        historical_messages = await agent_message_store.get(
            process_id=process_id,
        )
        for one_historical_message in historical_messages:
            yield json.dumps(asdict(one_historical_message)) + "\n"
        # subscribe

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    return StreamingResponse(
        message_generator(), media_type="application/x-ndjson", headers=headers
    )
