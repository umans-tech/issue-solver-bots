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
    CodeRepositoryIntegrationFailed,
    EnvironmentConfigurationProvided,
    EnvironmentConfigurationValidated,
    EnvironmentValidationFailed,
    IssueResolutionEnvironmentPrepared,
    NotionIntegrationAuthorized,
    NotionIntegrationTokenRefreshed,
    NotionIntegrationAuthorizationFailed,
    DocumentationPromptsDefined,
    DocumentationPromptsRemoved,
    DocumentationGenerationRequested,
    DocumentationGenerationStarted,
    DocumentationGenerationCompleted,
    DocumentationGenerationFailed,
)
from issue_solver.events.auto_documentation import AutoDocumentationSetup
from issue_solver.events.event_store import EventStore
from issue_solver.events.serializable_records import (
    ProcessTimelineEventRecords,
    serialize,
)
from issue_solver.webapi.dependencies import (
    get_event_store,
    get_logger,
    get_agent_message_store,
)

from issue_solver.webapi.payloads import BaseSchema

router = APIRouter(prefix="/processes", tags=["processes"])


class ProcessTimelineView(BaseSchema):
    id: str
    type: str
    status: str
    events: list[ProcessTimelineEventRecords]
    run_id: str | None = None

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
            run_id=cls.extract_run_id(events),
        )

    @classmethod
    def infer_process_type(cls, events: list[AnyDomainEvent]) -> str:
        if not events:
            raise ValueError("No events provided to infer process type.")
        first_event = events[0]
        if isinstance(first_event, IssueResolutionRequested):
            return "issue_resolution"
        if isinstance(first_event, EnvironmentConfigurationProvided):
            return "dev_environment_setup"
        if isinstance(first_event, NotionIntegrationAuthorized):
            return "notion_integration"
        if isinstance(
            first_event, (DocumentationPromptsDefined, DocumentationPromptsRemoved)
        ):
            return "docs_setup"
        if isinstance(
            first_event,
            (
                DocumentationGenerationRequested,
                DocumentationGenerationStarted,
                DocumentationGenerationCompleted,
                DocumentationGenerationFailed,
            ),
        ):
            return "docs_generation"
        return "code_repository_integration"

    @classmethod
    def to_status(cls, events: list[AnyDomainEvent]) -> str:
        status_affecting_events = [
            event
            for event in events
            if not isinstance(event, CodeRepositoryTokenRotated)
            and not isinstance(event, NotionIntegrationTokenRefreshed)
        ]

        if not status_affecting_events:
            return "unknown"

        status_affecting_events.sort(key=lambda event: event.occurred_at)
        last_event = status_affecting_events[-1]
        match last_event:
            case CodeRepositoryConnected() | NotionIntegrationAuthorized():
                status = "connected"
            case CodeRepositoryIndexed():
                status = "indexed"
            case RepositoryIndexationRequested():
                status = "indexing"
            case IssueResolutionEnvironmentPrepared():
                status = "starting"
            case IssueResolutionRequested():
                status = "requested"
            case IssueResolutionStarted():
                status = "in_progress"
            case IssueResolutionCompleted():
                status = "completed"
            case (
                IssueResolutionFailed()
                | CodeRepositoryIntegrationFailed()
                | EnvironmentValidationFailed()
                | NotionIntegrationAuthorizationFailed()
            ):
                status = "failed"
            case EnvironmentConfigurationProvided():
                status = "configuring"
            case EnvironmentConfigurationValidated():
                status = "ready"
            case DocumentationPromptsDefined():
                status = "configured"
            case DocumentationPromptsRemoved():
                status = (
                    "configured" if _auto_doc_prompts_remaining(events) else "removed"
                )
            case DocumentationGenerationRequested():
                status = "requested"
            case DocumentationGenerationStarted():
                status = "in_progress"
            case DocumentationGenerationCompleted():
                status = "completed"
            case DocumentationGenerationFailed():
                status = "failed"
            case _:
                status = "unknown"
        return status

    @classmethod
    def extract_run_id(cls, events: list[AnyDomainEvent]) -> str | None:
        for event in events:
            if isinstance(
                event,
                (
                    DocumentationGenerationRequested,
                    DocumentationGenerationStarted,
                    DocumentationGenerationCompleted,
                    DocumentationGenerationFailed,
                ),
            ):
                return getattr(event, "run_id", None)
        return None


class PaginatedProcessesResponse(BaseSchema):
    processes: list[ProcessTimelineView]
    total: int
    limit: int
    offset: int


@router.get("/")
async def list_processes(
    event_store: Annotated[EventStore, Depends(get_event_store)],
    space_id: str | None = Query(None, description="Filter by space ID"),
    knowledge_base_id: str | None = Query(
        None, description="Filter by knowledge base ID"
    ),
    process_type: str | None = Query(None, description="Filter by process type"),
    status: str | None = Query(None, description="Filter by status"),
    run_id: str | None = Query(None, description="Filter by run ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of processes to return"),
    offset: int = Query(0, ge=0, description="Number of processes to skip"),
) -> PaginatedProcessesResponse:
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
    filtered_processes = _apply_filters(processes, process_type, status, run_id)

    # Apply pagination
    total = len(filtered_processes)
    paginated_processes = filtered_processes[offset : offset + limit]

    return PaginatedProcessesResponse(
        processes=paginated_processes,
        total=total,
        limit=limit,
        offset=offset,
    )


async def _get_processes_by_criteria(
    event_store: EventStore, space_id: str | None, knowledge_base_id: str | None
) -> list[ProcessTimelineView]:
    """Get processes based on space_id or knowledge_base_id criteria."""
    processes = []

    if space_id:
        repo_events = await event_store.find(
            criteria={"space_id": space_id}, event_type=CodeRepositoryConnected
        )
        processes.extend(await _convert_events_to_processes(event_store, repo_events))

        notion_events = await event_store.find(
            criteria={"space_id": space_id}, event_type=NotionIntegrationAuthorized
        )
        processes.extend(await _convert_events_to_processes(event_store, notion_events))

        kb_ids = {event.knowledge_base_id for event in repo_events}
        processes.extend(await _get_auto_documentation_processes(event_store, kb_ids))
        processes.extend(await _get_doc_generation_processes(event_store, kb_ids))

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

        processes.extend(
            await _get_auto_documentation_processes(event_store, {knowledge_base_id})
        )

        processes.extend(
            await _get_doc_generation_processes(event_store, {knowledge_base_id})
        )

    return processes


def _apply_filters(
    processes: list[ProcessTimelineView],
    process_type: str | None,
    status: str | None,
    run_id: str | None,
) -> list[ProcessTimelineView]:
    """Apply type and status filters to processes."""
    filtered = processes

    if process_type:
        filtered = [p for p in filtered if p.type == process_type]

    if status:
        filtered = [p for p in filtered if p.status == status]

    if run_id:
        filtered = [p for p in filtered if p.run_id == run_id]

    return filtered


async def _get_all_processes(event_store: EventStore) -> list[ProcessTimelineView]:
    """Get all processes from all event types."""
    all_processes = []

    # Get all repository processes
    repo_events = await event_store.find(
        criteria={}, event_type=CodeRepositoryConnected
    )
    all_processes.extend(await _convert_events_to_processes(event_store, repo_events))

    # Get all Notion integration processes
    notion_events = await event_store.find(
        criteria={}, event_type=NotionIntegrationAuthorized
    )
    all_processes.extend(await _convert_events_to_processes(event_store, notion_events))

    # Get all issue resolution processes
    issue_events = await event_store.find(
        criteria={}, event_type=IssueResolutionRequested
    )
    all_processes.extend(await _convert_events_to_processes(event_store, issue_events))

    auto_doc_defined = await event_store.find(
        criteria={}, event_type=DocumentationPromptsDefined
    )
    auto_doc_removed = await event_store.find(
        criteria={}, event_type=DocumentationPromptsRemoved
    )
    all_processes.extend(
        await _convert_events_to_processes(
            event_store, [*auto_doc_defined, *auto_doc_removed]
        )
    )

    all_processes.extend(await _get_doc_generation_processes(event_store, None))

    return all_processes


async def _convert_events_to_processes(
    event_store: EventStore, events: list
) -> list[ProcessTimelineView]:
    """Convert domain events to process timeline views."""
    processes = []
    seen_processes: set[str] = set()
    for event in events:
        if event.process_id in seen_processes:
            continue
        process_events = await event_store.get(event.process_id)
        if not process_events:
            continue
        process_view = ProcessTimelineView.create_from(event.process_id, process_events)
        processes.append(process_view)
        seen_processes.add(event.process_id)
    return processes


def _auto_doc_prompts_remaining(events: list[AnyDomainEvent]) -> bool:
    doc_events = [
        event
        for event in events
        if isinstance(event, (DocumentationPromptsDefined, DocumentationPromptsRemoved))
    ]
    if not doc_events:
        return False
    knowledge_base_id = doc_events[0].knowledge_base_id
    setup = AutoDocumentationSetup.from_events(knowledge_base_id, doc_events)
    return bool(setup.docs_prompts)


async def _get_auto_documentation_processes(
    event_store: EventStore, knowledge_base_ids: set[str]
) -> list[ProcessTimelineView]:
    if not knowledge_base_ids:
        return []
    auto_doc_events: list[AnyDomainEvent] = []
    for kb_id in knowledge_base_ids:
        auto_doc_events.extend(
            await event_store.find(
                criteria={"knowledge_base_id": kb_id},
                event_type=DocumentationPromptsDefined,
            )
        )
        auto_doc_events.extend(
            await event_store.find(
                criteria={"knowledge_base_id": kb_id},
                event_type=DocumentationPromptsRemoved,
            )
        )
    return await _convert_events_to_processes(event_store, auto_doc_events)


async def _get_doc_generation_processes(
    event_store: EventStore, knowledge_base_ids: set[str] | None
) -> list[ProcessTimelineView]:
    doc_events: list[AnyDomainEvent] = []
    if knowledge_base_ids is None:
        doc_events = await event_store.find(
            criteria={}, event_type=DocumentationGenerationRequested
        )
    elif not knowledge_base_ids:
        return []
    else:
        for kb_id in knowledge_base_ids:
            doc_events.extend(
                await event_store.find(
                    criteria={"knowledge_base_id": kb_id},
                    event_type=DocumentationGenerationRequested,
                )
            )
    return await _convert_events_to_processes(event_store, doc_events)


@router.get(
    "/{process_id}",
    response_model=ProcessTimelineView,
    response_model_exclude_none=True,
)
async def get_process(
    process_id: str,
    event_store: Annotated[EventStore, Depends(get_event_store)],
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
