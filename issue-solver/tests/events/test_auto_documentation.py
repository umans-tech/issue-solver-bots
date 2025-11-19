from datetime import datetime

import pytest

from issue_solver.events.auto_documentation import (
    AutoDocumentationSetup,
    CannotRemoveAutoDocumentationWithoutPrompts,
    CannotRemoveUnknownAutoDocumentationPrompts,
    load_auto_documentation_setup,
)
from issue_solver.events.domain import (
    DocumentationPromptsDefined,
    DocumentationPromptsRemoved,
)


def test_auto_documentation_setup_from_events_filters_blank_prompts():
    # Given
    knowledge_base_id = "kb-auto-doc-01"
    events = [
        DocumentationPromptsDefined(
            knowledge_base_id=knowledge_base_id,
            user_id="doc-bot",
            docs_prompts={
                "runbook": "Write a runbook",
                "overview": "Create an overview",
            },
            process_id="process-a",
            occurred_at=datetime.fromisoformat("2025-01-10T10:00:00+00:00"),
        ),
        DocumentationPromptsDefined(
            knowledge_base_id=knowledge_base_id,
            user_id="doc-bot",
            docs_prompts={"overview": ""},
            process_id="process-b",
            occurred_at=datetime.fromisoformat("2025-01-10T11:00:00+00:00"),
        ),
    ]

    # When
    setup = AutoDocumentationSetup.from_events(knowledge_base_id, events)

    # Then
    assert setup.docs_prompts == {"runbook": "Write a runbook"}
    assert setup.last_process_id == "process-b"
    assert setup.updated_at == events[-1].occurred_at


def test_auto_documentation_setup_apply_returns_new_state():
    # Given
    knowledge_base_id = "kb-auto-doc-apply"
    setup = AutoDocumentationSetup.start(knowledge_base_id)
    first_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={"overview": "Initial"},
        process_id="process-initial",
        occurred_at=datetime.fromisoformat("2025-02-01T09:00:00+00:00"),
    )
    second_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={"overview": "Refined", "adr": "Capture ADR"},
        process_id="process-update",
        occurred_at=datetime.fromisoformat("2025-02-01T10:30:00+00:00"),
    )
    removal_event = DocumentationPromptsRemoved(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        prompt_ids={"overview"},
        process_id="process-remove",
        occurred_at=datetime.fromisoformat("2025-02-01T11:00:00+00:00"),
    )

    # When
    intermediate = setup.apply(first_event)
    updated = intermediate.apply(second_event)
    after_removal = updated.apply(removal_event)

    # Then
    assert intermediate.docs_prompts == {"overview": "Initial"}
    assert updated.docs_prompts == {
        "overview": "Refined",
        "adr": "Capture ADR",
    }
    assert updated.last_process_id == "process-update"
    assert updated.updated_at == second_event.occurred_at
    assert after_removal.docs_prompts == {"adr": "Capture ADR"}
    assert after_removal.last_process_id == "process-remove"


def test_auto_documentation_setup_from_events_handles_empty_sequence():
    # Given
    knowledge_base_id = "kb-empty"

    # When
    setup = AutoDocumentationSetup.from_events(knowledge_base_id, [])

    # Then
    assert setup == AutoDocumentationSetup.start(knowledge_base_id)


def test_auto_documentation_setup_prevents_removal_when_no_prompts_exist():
    # Given
    setup = AutoDocumentationSetup.start("kb-ensure")

    # When / Then
    with pytest.raises(CannotRemoveAutoDocumentationWithoutPrompts):
        setup.ensure_prompt_ids_can_be_removed({"overview"})


def test_auto_documentation_setup_prevents_removal_of_unknown_prompts():
    # Given
    setup = AutoDocumentationSetup.start("kb-ensure").apply(
        DocumentationPromptsDefined(
            knowledge_base_id="kb-ensure",
            user_id="doc-bot",
            docs_prompts={"overview": "Write overview"},
            process_id="process",
            occurred_at=datetime.fromisoformat("2025-05-01T10:00:00+00:00"),
        )
    )

    # When / Then
    with pytest.raises(CannotRemoveUnknownAutoDocumentationPrompts) as exc_info:
        setup.ensure_prompt_ids_can_be_removed(["missing"])
    assert exc_info.value.prompt_ids == ["missing"]


def test_auto_documentation_setup_cannot_apply_removal_before_any_definition():
    # Given
    setup = AutoDocumentationSetup.start("kb-remove-first")
    removal_event = DocumentationPromptsRemoved(
        knowledge_base_id="kb-remove-first",
        user_id="doc-bot",
        prompt_ids={"overview"},
        process_id="process-remove",
        occurred_at=datetime.fromisoformat("2025-05-02T09:00:00+00:00"),
    )

    # When / Then
    with pytest.raises(CannotRemoveAutoDocumentationWithoutPrompts):
        setup.apply(removal_event)


@pytest.mark.asyncio
async def test_load_auto_documentation_setup_tracks_latest_metadata(event_store):
    # Given
    knowledge_base_id = "kb-auto-doc-02"
    first_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={"overview": "Initial"},
        process_id="process-initial",
        occurred_at=datetime.fromisoformat("2025-01-01T09:00:00+00:00"),
    )
    second_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={"overview": "Refined"},
        process_id="process-update",
        occurred_at=datetime.fromisoformat("2025-01-01T10:30:00+00:00"),
    )
    removal_event = DocumentationPromptsRemoved(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        prompt_ids={"overview"},
        process_id="process-remove",
        occurred_at=datetime.fromisoformat("2025-01-01T11:00:00+00:00"),
    )
    await event_store.append(first_event.process_id, first_event)
    await event_store.append(second_event.process_id, second_event)
    await event_store.append(removal_event.process_id, removal_event)

    # When
    setup = await load_auto_documentation_setup(event_store, knowledge_base_id)

    # Then
    assert setup.docs_prompts == {}
    assert setup.updated_at == removal_event.occurred_at
    assert setup.last_process_id == removal_event.process_id
