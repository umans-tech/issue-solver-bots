import logging

from fastapi import APIRouter

from issue_solver.events.serializable_records import ProcessTimelineEventRecords
from issue_solver.queueing.sqs_events_publishing import publish

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/events", status_code=200)
async def notify_event_received(event: ProcessTimelineEventRecords) -> None:
    """Endpoint to receive webhook events."""
    domain_event = event.to_domain_event()
    publish(domain_event, logger=logging.getLogger(__name__))
