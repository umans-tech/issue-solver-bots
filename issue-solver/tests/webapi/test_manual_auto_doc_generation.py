import pytest
from datetime import datetime
from fastapi import HTTPException

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    DocumentationPromptsDefined,
    DocumentationGenerationRequested,
)
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.webapi.routers.repository import trigger_auto_document_generation
from issue_solver.webapi.payloads import AutoDocManualGenerationRequest
from tests.controllable_clock import ControllableClock


@pytest.mark.asyncio
async def test_manual_auto_doc_emits_request_event():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))
    kb_id = "kb-manual"

    await event_store.append(
        "conn",
        CodeRepositoryConnected(
            url="https://example.com/repo.git",
            access_token="token",
            user_id="user-1",
            space_id="space-1",
            knowledge_base_id=kb_id,
            process_id="conn",
            occurred_at=clock.now(),
            token_permissions=None,
        ),
    )
    await event_store.append(
        "indexed",
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="commit-123",
            stats={},
            knowledge_base_id=kb_id,
            process_id="indexed",
            occurred_at=clock.now(),
        ),
    )
    await event_store.append(
        "prompts",
        DocumentationPromptsDefined(
            knowledge_base_id=kb_id,
            user_id="user-1",
            docs_prompts={"overview.md": "Write overview"},
            process_id="prompts",
            occurred_at=clock.now(),
        ),
    )

    request = AutoDocManualGenerationRequest(prompt_id="overview.md", mode="update")
    # When
    result = await trigger_auto_document_generation(
        knowledge_base_id=kb_id,
        request=request,
        user_id="user-1",
        event_store=event_store,
        clock=clock,
    )

    # Then
    assert "process_id" in result and "run_id" in result
    events = await event_store.get(result["process_id"])
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, DocumentationGenerationRequested)
    assert event.mode == "update"
    assert event.code_version == "commit-123"
    assert event.prompt_id == "overview.md"


@pytest.mark.asyncio
async def test_manual_auto_doc_returns_404_when_prompt_missing():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))

    await event_store.append(
        "conn",
        CodeRepositoryConnected(
            url="https://example.com/repo.git",
            access_token="token",
            user_id="user-1",
            space_id="space-1",
            knowledge_base_id="kb-missing",
            process_id="conn",
            occurred_at=clock.now(),
            token_permissions=None,
        ),
    )
    request = AutoDocManualGenerationRequest(prompt_id="missing.md", mode="complete")
    # When
    with pytest.raises(HTTPException) as exc:
        await trigger_auto_document_generation(
            knowledge_base_id="kb-missing",
            request=request,
            user_id="user-1",
            event_store=event_store,
            clock=clock,
        )
    # Then
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_manual_auto_doc_returns_409_when_repo_not_indexed():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))
    kb_id = "kb-no-index"

    await event_store.append(
        "conn",
        CodeRepositoryConnected(
            url="https://example.com/repo.git",
            access_token="token",
            user_id="user-1",
            space_id="space-1",
            knowledge_base_id=kb_id,
            process_id="conn",
            occurred_at=clock.now(),
            token_permissions=None,
        ),
    )
    await event_store.append(
        "prompts",
        DocumentationPromptsDefined(
            knowledge_base_id=kb_id,
            user_id="user-1",
            docs_prompts={"overview.md": "Write overview"},
            process_id="prompts",
            occurred_at=clock.now(),
        ),
    )

    request = AutoDocManualGenerationRequest(prompt_id="overview.md", mode="update")
    # When
    with pytest.raises(HTTPException) as exc:
        await trigger_auto_document_generation(
            knowledge_base_id=kb_id,
            request=request,
            user_id="user-1",
            event_store=event_store,
            clock=clock,
        )
    # Then
    assert exc.value.status_code == 409
