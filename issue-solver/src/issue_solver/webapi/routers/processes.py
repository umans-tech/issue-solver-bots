import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends

from issue_solver.events.in_memory_event_store import InMemoryEventStore
from issue_solver.webapi.dependencies import get_event_store

# Get logger for your module
logger = logging.getLogger("issue_solver.webapi.routers.processes")
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/processes", tags=["processes"])


@router.get("/{process_id}")
def get_process(
    process_id: str,
    event_store: Annotated[InMemoryEventStore, Depends(get_event_store)],
):
    """Get information about a specific process."""
    process_events = event_store.get(process_id)
    if not process_events:
        raise HTTPException(status_code=404, detail="Process not found")

    return {"process_id": process_id, "events_count": len(process_events)} 