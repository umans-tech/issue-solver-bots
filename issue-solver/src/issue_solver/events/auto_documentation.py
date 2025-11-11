from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from issue_solver.events.domain import DocumentationPromptsDefined
from issue_solver.events.event_store import EventStore


AUTO_DOC_PROCESS_PREFIX = "auto-documentation:"


def auto_documentation_process_id(knowledge_base_id: str) -> str:
    """Return a stable process identifier for a knowledge base."""

    return f"{AUTO_DOC_PROCESS_PREFIX}{knowledge_base_id}"


@dataclass(slots=True)
class AutoDocumentationState:
    knowledge_base_id: str
    docs_prompts: dict[str, str]
    updated_at: datetime | None
    last_process_id: str | None


async def load_auto_documentation_state(
    event_store: EventStore, knowledge_base_id: str
) -> AutoDocumentationState:
    """Merge prompt definitions for a knowledge base and expose metadata."""

    doc_events = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, DocumentationPromptsDefined
    )
    doc_events.sort(key=lambda event: event.occurred_at)

    merged_prompts: dict[str, str] = {}
    latest_event: DocumentationPromptsDefined | None = None

    for event in doc_events:
        merged_prompts.update(event.docs_prompts)
        latest_event = event

    filtered_prompts = {
        key: value
        for key, value in merged_prompts.items()
        if isinstance(value, str) and value.strip()
    }

    return AutoDocumentationState(
        knowledge_base_id=knowledge_base_id,
        docs_prompts=filtered_prompts,
        updated_at=latest_event.occurred_at if latest_event else None,
        last_process_id=latest_event.process_id if latest_event else None,
    )
