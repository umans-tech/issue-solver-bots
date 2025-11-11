from datetime import datetime

import pytest

from issue_solver.events.auto_documentation import (
    auto_documentation_process_id,
    load_auto_documentation_setup,
)
from issue_solver.events.domain import DocumentationPromptsDefined
from issue_solver.events.event_store import InMemoryEventStore


@pytest.fixture
def event_store() -> InMemoryEventStore:
    return InMemoryEventStore()


def test_auto_documentation_process_id_is_deterministic():
    # Given
    knowledge_base_id = "kb-456"

    # When
    first = auto_documentation_process_id(knowledge_base_id)
    second = auto_documentation_process_id(knowledge_base_id)

    # Then
    assert first == second
    assert knowledge_base_id in first


@pytest.mark.asyncio
async def test_load_auto_documentation_setup_filters_blank_prompts(event_store):
    # Given
    knowledge_base_id = "kb-auto-doc-01"
    first_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={
            "runbook": "Write a runbook",
            "overview": "Create an overview",
        },
        process_id=auto_documentation_process_id(knowledge_base_id),
        occurred_at=datetime.fromisoformat("2025-01-10T10:00:00+00:00"),
    )
    removal_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={"overview": ""},
        process_id=auto_documentation_process_id(knowledge_base_id),
        occurred_at=datetime.fromisoformat("2025-01-10T11:00:00+00:00"),
    )
    await event_store.append(first_event.process_id, first_event)
    await event_store.append(removal_event.process_id, removal_event)

    # When
    setup = await load_auto_documentation_setup(event_store, knowledge_base_id)

    # Then
    assert setup.docs_prompts == {"runbook": "Write a runbook"}


@pytest.mark.asyncio
async def test_load_auto_documentation_setup_tracks_latest_metadata(event_store):
    # Given
    knowledge_base_id = "kb-auto-doc-02"
    process_id = auto_documentation_process_id(knowledge_base_id)
    first_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={"overview": "Initial"},
        process_id=process_id,
        occurred_at=datetime.fromisoformat("2025-01-01T09:00:00+00:00"),
    )
    second_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={"overview": "Refined"},
        process_id=process_id,
        occurred_at=datetime.fromisoformat("2025-01-01T10:30:00+00:00"),
    )
    await event_store.append(process_id, first_event)
    await event_store.append(process_id, second_event)

    # When
    setup = await load_auto_documentation_setup(event_store, knowledge_base_id)

    # Then
    assert setup.docs_prompts == {"overview": "Refined"}
    assert setup.updated_at == second_event.occurred_at
    assert setup.last_process_id == process_id
