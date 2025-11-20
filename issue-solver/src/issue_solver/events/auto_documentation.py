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


class AutoDocumentationError(Exception):
    """Base error for auto-documentation aggregates."""


class CannotRemoveAutoDocumentationWithoutPrompts(AutoDocumentationError):
    def __init__(self, knowledge_base_id: str):
        self.knowledge_base_id = knowledge_base_id
        super().__init__(
            f"Cannot remove auto-documentation prompts because none exist for knowledge base {knowledge_base_id}."
        )


class CannotRemoveUnknownAutoDocumentationPrompts(AutoDocumentationError):
    def __init__(self, prompt_ids: Sequence[str]):
        self.prompt_ids = list(prompt_ids)
        formatted = ", ".join(self.prompt_ids)
        super().__init__(
            f"Cannot remove unknown auto-documentation prompts: {formatted}"
        )


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
        next_prompts = self._next_prompts_after(event)
        return replace(
            self,
            docs_prompts=next_prompts,
            updated_at=event.occurred_at,
            last_process_id=event.process_id,
        )

    def ensure_prompt_ids_can_be_removed(self, prompt_ids: set[str]) -> None:
        if not self.docs_prompts:
            raise CannotRemoveAutoDocumentationWithoutPrompts(self.knowledge_base_id)
        missing = [pid for pid in prompt_ids if pid not in self.docs_prompts]
        if missing:
            raise CannotRemoveUnknownAutoDocumentationPrompts(missing)

    def _next_prompts_after(self, event: AutoDocumentationEvent) -> dict[str, str]:
        match event:
            case DocumentationPromptsRemoved(prompt_ids=prompt_ids):
                return self._without(prompt_ids)
            case DocumentationPromptsDefined(docs_prompts=new_prompts):
                return self._merged_with(new_prompts)
            case _:
                assert_never(event)

    def _without(self, prompt_ids: set[str]) -> dict[str, str]:
        self.ensure_prompt_ids_can_be_removed(prompt_ids)
        next_prompts = self.docs_prompts.copy()
        for prompt_id in prompt_ids:
            next_prompts.pop(prompt_id)
        return next_prompts

    def _merged_with(self, new_prompts: dict[str, str]) -> dict[str, str]:
        merged = self.docs_prompts | new_prompts
        return {key: value for key, value in merged.items() if value.strip()}

    def prompt_matches(self, prompt_id: str, prompt_description: str) -> bool:
        return self.docs_prompts.get(prompt_id) == prompt_description


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
