import logging
from datetime import datetime

import pytest
from fastapi import HTTPException

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    DocumentationPromptsDefined,
    DocumentationGenerationCompleted,
)
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.webapi.payloads import AutoDocPublishCompletedRequest
from issue_solver.webapi.routers.repository import (
    get_latest_auto_documentation_commit,
    record_auto_documentation_publish,
)
from tests.controllable_clock import ControllableClock


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
async def test_publish_completed_records_generation_completed_event():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))
    kb_id = "kb-auto-doc-publish"

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
    await event_store.append(
        "prompts",
        DocumentationPromptsDefined(
            knowledge_base_id=kb_id,
            user_id="user-1",
            docs_prompts={"overview": "Summarize the system"},
            process_id="prompts",
            occurred_at=clock.now(),
        ),
    )

    request = AutoDocPublishCompletedRequest(
        prompt_id="overview",
        code_version="commit-123",
        generated_documents=["overview.md"],
        process_id="publish-1",
        run_id="run-1",
    )

    # When
    result = await record_auto_documentation_publish(
        knowledge_base_id=kb_id,
        request=request,
        user_id="user-1",
        event_store=event_store,
        clock=clock,
        logger=logging.getLogger("test"),
    )

    # Then
    assert result["process_id"] == "publish-1"
    assert result["run_id"] == "run-1"

    events = await event_store.get("publish-1")
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, DocumentationGenerationCompleted)
    assert event.prompt_id == "overview"
    assert event.code_version == "commit-123"
    assert event.generated_documents == ["overview.md"]


@pytest.mark.asyncio
async def test_publish_completed_returns_404_when_prompt_missing():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))
    kb_id = "kb-auto-doc-missing-prompt"

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

    request = AutoDocPublishCompletedRequest(
        prompt_id="overview",
        code_version="commit-123",
        generated_documents=["overview.md"],
    )

    # When
    with pytest.raises(HTTPException) as exc:
        await record_auto_documentation_publish(
            knowledge_base_id=kb_id,
            request=request,
            user_id="user-1",
            event_store=event_store,
            clock=clock,
            logger=logging.getLogger("test"),
        )

    # Then
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_publish_completed_returns_409_when_commit_is_stale():
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime.fromisoformat("2025-01-01T00:00:00+00:00"))
    kb_id = "kb-auto-doc-stale"

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
    await event_store.append(
        "prompts",
        DocumentationPromptsDefined(
            knowledge_base_id=kb_id,
            user_id="user-1",
            docs_prompts={"overview": "Summarize the system"},
            process_id="prompts",
            occurred_at=clock.now(),
        ),
    )

    request = AutoDocPublishCompletedRequest(
        prompt_id="overview",
        code_version="commit-older",
        generated_documents=["overview.md"],
    )

    # When
    with pytest.raises(HTTPException) as exc:
        await record_auto_documentation_publish(
            knowledge_base_id=kb_id,
            request=request,
            user_id="user-1",
            event_store=event_store,
            clock=clock,
            logger=logging.getLogger("test"),
        )

    # Then
    assert exc.value.status_code == 409
