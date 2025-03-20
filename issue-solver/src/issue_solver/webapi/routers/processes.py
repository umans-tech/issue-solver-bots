import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends

from issue_solver.events.in_memory_event_store import InMemoryEventStore
from issue_solver.webapi.dependencies import get_event_store, get_logger

router = APIRouter(prefix="/processes", tags=["processes"])


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
):
    """Get information about a specific process."""
    logger.info(f"Retrieving information for process ID: {process_id}")
    process_events = event_store.get(process_id)
    if not process_events:
        logger.warning(f"Process ID not found: {process_id}")
        raise HTTPException(status_code=404, detail="Process not found")

    logger.info(f"Found process with {len(process_events)} events")
    return {"process_id": process_id, "events_count": len(process_events)}
