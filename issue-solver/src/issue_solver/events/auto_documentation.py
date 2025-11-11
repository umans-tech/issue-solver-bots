from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Sequence

from issue_solver.events.domain import DocumentationPromptsDefined
from issue_solver.events.event_store import EventStore


@dataclass(slots=True)
class AutoDocumentationSetup:
    knowledge_base_id: str
    docs_prompts: dict[str, str]
    updated_at: datetime | None
    last_process_id: str | None

    @classmethod
    def start(cls, knowledge_base_id: str) -> "AutoDocumentationSetup":
        return cls(
            knowledge_base_id=knowledge_base_id,
            docs_prompts={},
            updated_at=None,
            last_process_id=None,
        )

    @classmethod
    def from_events(
        cls,
        knowledge_base_id: str,
        events: Sequence[DocumentationPromptsDefined],
    ) -> "AutoDocumentationSetup":
        events_sorted = sorted(events, key=lambda event: event.occurred_at)
        setup = cls.start(knowledge_base_id)
        for event in events_sorted:
            setup = setup.apply(event)
        return setup

    def apply(self, event: DocumentationPromptsDefined) -> "AutoDocumentationSetup":
        updated_prompts = self.docs_prompts | event.docs_prompts
        filtered_prompts = {
            key: value
            for key, value in updated_prompts.items()
            if isinstance(value, str) and value.strip()
        }
        return replace(
            self,
            docs_prompts=filtered_prompts,
            updated_at=event.occurred_at,
            last_process_id=event.process_id,
        )


async def load_auto_documentation_setup(
    event_store: EventStore, knowledge_base_id: str
) -> AutoDocumentationSetup:
    """Merge prompt definitions for a knowledge base and expose metadata."""

    doc_events = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, DocumentationPromptsDefined
    )
    return AutoDocumentationSetup.from_events(knowledge_base_id, doc_events)
