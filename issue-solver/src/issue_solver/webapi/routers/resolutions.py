import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from issue_solver.clock import Clock
from issue_solver.events.domain import (
    IssueResolutionRequested,
)
from issue_solver.events.event_store import EventStore
from issue_solver.webapi.dependencies import (
    get_logger,
    get_event_store,
    get_clock,
    get_user_id_or_default,
)
from issue_solver.webapi.payloads import (
    ResolveIssueRequest,
    ProcessCreated,
)

router = APIRouter(prefix="/resolutions", tags=["resolutions"])


@router.post("/", status_code=201)
async def resolve_issue(
    request: ResolveIssueRequest,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.repository.index")),
    ],
) -> ProcessCreated:
    """Request issue resolution for a given knowledge base and issue."""
    process_id = str(uuid.uuid4())
    knowledge_base_id = request.knowledge_base_id
    event = IssueResolutionRequested(
        occurred_at=clock.now(),
        knowledge_base_id=knowledge_base_id,
        process_id=process_id,
        issue=request.issue,
        user_id=user_id,
        agent=request.agent,
        max_turns=request.max_turns,
        ai_model=request.ai_model,
        ai_model_version=request.ai_model_version,
        execution_environment=request.execution_environment,
    )
    await event_store.append(process_id, event)
    return ProcessCreated(process_id=process_id)
