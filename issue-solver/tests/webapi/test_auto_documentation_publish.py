import logging
from datetime import datetime

import pytest
from fastapi import HTTPException

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    DocumentationGenerationCompleted,
    DocumentationPromptsDefined,
)
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.webapi.payloads import AutoDocPublishRequest
from issue_solver.webapi.routers.repository import (
    get_latest_auto_documentation_commit,
    publish_auto_documentation,
)
from issue_solver.worker.documenting.knowledge_repository import KnowledgeBase
from tests.controllable_clock import ControllableClock
from tests.fixtures import InMemoryKnowledgeRepository


def build_connected_repo(kb_id: str, occurred_at: datetime):
    return CodeRepositoryConnected(
        url="https://example.com/repo.git",
        access_token="token",
        user_id="user-1",
        space_id="space-1",
        knowledge_base_id=kb_id,
        process_id="conn",
        occurred_at=occurred_at,
        token_permissions=None,
    )


@pytest.mark.asyncio
async def test_latest_indexed_commit_returns_latest_commit():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))
    kb_id = "kb-auto-doc-latest"

    await event_store.append("conn", build_connected_repo(kb_id, clock.now()))
    await event_store.append(
        "indexed-1",
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="commit-111",
            stats={},
            knowledge_base_id=kb_id,
            process_id="indexed-1",
            occurred_at=clock.now(),
        ),
    )
    clock.set_from_iso_format("2025-01-02T00:00:00+00:00")
    await event_store.append(
        "indexed-2",
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="commit-222",
            stats={},
            knowledge_base_id=kb_id,
            process_id="indexed-2",
            occurred_at=clock.now(),
        ),
    )

    # When
    result = await get_latest_auto_documentation_commit(
        knowledge_base_id=kb_id,
        event_store=event_store,
        logger=logging.getLogger("test"),
    )

    # Then
    assert result["commit_sha"] == "commit-222"


@pytest.mark.asyncio
async def test_latest_indexed_commit_returns_409_when_missing():
    # Given
    event_store = InMemoryEventStore()
    kb_id = "kb-auto-doc-missing"
    await event_store.append(
        "conn",
        build_connected_repo(
            kb_id, datetime.fromisoformat("2025-01-01T00:00:00+00:00")
        ),
    )

    # When
    with pytest.raises(HTTPException) as exc:
        await get_latest_auto_documentation_commit(
            knowledge_base_id=kb_id,
            event_store=event_store,
            logger=logging.getLogger("test"),
        )

    # Then
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_publish_auto_documentation_stores_doc_and_records_events():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))
    kb_id = "kb-auto-doc-publish"
    knowledge_repository = InMemoryKnowledgeRepository()

    await event_store.append("conn", build_connected_repo(kb_id, clock.now()))
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

    request = AutoDocPublishRequest(
        path="architecture/overview",
        content="## Overview\nApproved content.",
        prompt_description="Summarize the architecture for onboarding.",
        title="Architecture Overview",
        source={
            "source": "conversation",
            "chat_id": "chat-1",
            "message_id": "msg-1",
        },
    )

    # When
    result = await publish_auto_documentation(
        knowledge_base_id=kb_id,
        request=request,
        user_id="user-1",
        event_store=event_store,
        clock=clock,
        knowledge_repository=knowledge_repository,
        logger=logging.getLogger("test"),
    )

    # Then
    assert result["prompt_id"] == "architecture/overview"
    assert result["code_version"] == "commit-123"
    assert result["generated_documents"] == ["architecture/overview.md"]

    stored_content = knowledge_repository.get_content(
        KnowledgeBase(kb_id, "commit-123"), "architecture/overview.md"
    )
    assert "Approved content" in stored_content

    stored_metadata = knowledge_repository.get_metadata(
        KnowledgeBase(kb_id, "commit-123"), "architecture/overview.md"
    )
    assert stored_metadata["origin"] == "auto"
    assert stored_metadata["source"] == "conversation"
    assert stored_metadata["chat_id"] == "chat-1"
    assert stored_metadata["message_id"] == "msg-1"

    prompts_events = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationPromptsDefined
    )
    assert prompts_events
    assert prompts_events[-1].docs_prompts == {
        "architecture/overview": "Summarize the architecture for onboarding."
    }

    generation_events = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationGenerationCompleted
    )
    assert generation_events
    assert generation_events[-1].generated_documents == ["architecture/overview.md"]


@pytest.mark.asyncio
async def test_publish_auto_documentation_returns_409_when_repo_not_indexed():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))
    kb_id = "kb-auto-doc-no-index"
    knowledge_repository = InMemoryKnowledgeRepository()

    await event_store.append("conn", build_connected_repo(kb_id, clock.now()))

    request = AutoDocPublishRequest(
        path="overview",
        content="Docs",
        prompt_description="Summarize the repo.",
    )

    # When
    with pytest.raises(HTTPException) as exc:
        await publish_auto_documentation(
            knowledge_base_id=kb_id,
            request=request,
            user_id="user-1",
            event_store=event_store,
            clock=clock,
            knowledge_repository=knowledge_repository,
            logger=logging.getLogger("test"),
        )

    # Then
    assert exc.value.status_code == 409
