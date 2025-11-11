from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Sequence, assert_never

from issue_solver.events.domain import (
    DocumentationPromptsDefined,
    DocumentationPromptsRemoved,
)
from issue_solver.events.event_store import EventStore


AutoDocumentationEvent = DocumentationPromptsDefined | DocumentationPromptsRemoved


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
        events: Sequence[AutoDocumentationEvent],
    ) -> "AutoDocumentationSetup":
        events_sorted = sorted(events, key=lambda event: event.occurred_at)
        setup = cls.start(knowledge_base_id)
        for event in events_sorted:
            setup = setup.apply(event)
        return setup

    def apply(self, event: AutoDocumentationEvent) -> "AutoDocumentationSetup":
        match event:
            case DocumentationPromptsRemoved(prompt_ids=prompt_ids):
                removed = set(prompt_ids)
                next_prompts = {
                    key: value
                    for key, value in self.docs_prompts.items()
                    if key not in removed
                }
            case DocumentationPromptsDefined(docs_prompts=new_prompts):
                merged = self.docs_prompts | new_prompts
                next_prompts = {
                    key: value
                    for key, value in merged.items()
                    if isinstance(value, str) and value.strip()
                }
            case _:
                assert_never(event)
        return replace(
            self,
            docs_prompts=next_prompts,
            updated_at=event.occurred_at,
            last_process_id=event.process_id,
        )


async def load_auto_documentation_setup(
    event_store: EventStore, knowledge_base_id: str
) -> AutoDocumentationSetup:
    """Merge prompt definitions for a knowledge base and expose metadata."""

    defined_events = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, DocumentationPromptsDefined
    )
    removal_events = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, DocumentationPromptsRemoved
    )
    return AutoDocumentationSetup.from_events(
        knowledge_base_id, [*defined_events, *removal_events]
    )
