import os
from datetime import datetime

import pytest

from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.env_setup.dev_environments_management import (
    ExecutionEnvironmentPreference,
)
from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    IssueResolutionRequested,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    AnyDomainEvent,
    IssueResolutionFailed,
    EnvironmentConfigurationProvided,
    IssueResolutionEnvironmentPrepared,
)
from issue_solver.events.event_store import EventStore
from issue_solver.issues.issue import IssueInfo
from issue_solver.models.supported_models import SupportedOpenAIModel
from tests.examples.happy_path_persona import examples_of_all_events


@pytest.mark.parametrize(
    "event_type,event",
    examples_of_all_events(),
)
@pytest.mark.asyncio
async def test_should_persist_events_of_each_type(
    event_type: str, event: AnyDomainEvent, event_store: EventStore
):
    # When
    await event_store.append(event.process_id, event)

    # Then
    retrieved_events = await event_store.get(event.process_id)
    assert retrieved_events == [event]


@pytest.mark.asyncio
async def test_find_should_return_events_with_matching_criteria(
    event_store: EventStore,
):
    # Given
    appended_event = CodeRepositoryConnected(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        url="https://github.com/test/repo",
        access_token="s3c3t-3t0k3n",
        user_id="test-user-id",
        space_id="test-space-id",
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    found_events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
            "user_id": "test-user-id",
        },
        event_type=CodeRepositoryConnected,
    )

    # Then
    assert found_events == [appended_event]


@pytest.mark.asyncio
async def test_find_should_return_empty_list_when_no_events_match_criteria(
    event_store: EventStore,
):
    # Given
    appended_event = CodeRepositoryConnected(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        url="https://github.com/test/repo",
        access_token="s3c3t-3t0k3n",
        user_id="test-user-id",
        space_id="test-space-id",
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    found_events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
            "user_id": "unknown-user-id",
        },
        event_type=CodeRepositoryConnected,
    )

    # Then
    assert not found_events


@pytest.mark.asyncio
async def test_find_should_return_empty_list_when_event_type_does_not_match(
    event_store: EventStore,
):
    # Given
    appended_event = CodeRepositoryConnected(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        url="https://github.com/test/repo",
        access_token="s3c3t-3t0k3n",
        user_id="test-user-id",
        space_id="test-space-id",
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    found_events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
        },
        event_type=CodeRepositoryIndexed,
    )

    # Then
    assert not found_events


@pytest.mark.asyncio
async def test_get_event_repository_indexation_requested(event_store: EventStore):
    # Given
    appended_event = RepositoryIndexationRequested(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
        user_id="test-user-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    events = await event_store.get("test-process-id")

    # Then
    assert events == [appended_event]


@pytest.mark.asyncio
async def test_find_event_repository_indexation_requested(event_store: EventStore):
    # Given
    appended_event = RepositoryIndexationRequested(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
        user_id="test-user-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
        },
        event_type=RepositoryIndexationRequested,
    )

    # Then
    assert events == [appended_event]


@pytest.mark.asyncio
async def test_get_issue_resolution_events(
    event_store: EventStore,
):
    # Given
    events: list[AnyDomainEvent] = [
        IssueResolutionRequested(
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            issue=IssueInfo(description="test issue"),
            user_id="test-user-id",
        ),
        IssueResolutionStarted(
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
            process_id="test-process-id",
        ),
        IssueResolutionCompleted(
            occurred_at=datetime.fromisoformat("2021-01-01T02:00:00"),
            process_id="test-process-id",
            pr_url="test-pr-url",
            pr_number=123,
        ),
    ]

    await event_store.append("test-process-id", *events)

    # When
    retrieved_events = await event_store.get("test-process-id")

    # Then
    assert retrieved_events == events


@pytest.mark.asyncio
async def test_get_issue_resolution_events_2(
    event_store: EventStore,
):
    # Given
    events: list[AnyDomainEvent] = [
        IssueResolutionRequested(
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            issue=IssueInfo(description="test issue"),
        ),
        IssueResolutionStarted(
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
            process_id="test-process-id",
        ),
        IssueResolutionFailed(
            occurred_at=datetime.fromisoformat("2021-01-01T02:00:00"),
            process_id="test-process-id",
            reason="test reason",
            error_message="test error message",
        ),
    ]

    await event_store.append("test-process-id", *events)

    # When
    retrieved_events = await event_store.get("test-process-id")

    # Then
    assert retrieved_events == events


@pytest.mark.asyncio
async def test_get_events_with_encrypted_tokens(
    event_store: EventStore, generated_encryption_key: str
):
    # Given
    os.environ["TOKEN_ENCRYPTION_KEY"] = generated_encryption_key
    appended_event = CodeRepositoryConnected(
        occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        url="https://github.com/test/repo",
        access_token="s3c3t-3t0k3n",
        user_id="test-user-id",
        space_id="test-space-id",
        knowledge_base_id="knowledge-base-id",
        process_id="test-process-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    found_events = await event_store.get("test-process-id")

    # Then
    assert found_events == [appended_event]


@pytest.mark.asyncio
async def test_get_issue_resolution_events_with_dev_environment_configuration(
    event_store: EventStore,
):
    # Given
    events: list[AnyDomainEvent] = [
        IssueResolutionRequested(
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            issue=IssueInfo(description="test issue"),
            user_id="test-user-id",
        ),
        EnvironmentConfigurationProvided(
            occurred_at=datetime.fromisoformat("2021-01-01T00:30:00"),
            process_id="test-process-id",
            environment_id="dev-environment-id-xyz",
            user_id="test-user-id",
            project_setup="apt update && apt install -y python3 \n pip install -e .'[dev]'",
            knowledge_base_id="knowledge-base-id",
        ),
        IssueResolutionStarted(
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
            process_id="test-process-id",
        ),
        IssueResolutionCompleted(
            occurred_at=datetime.fromisoformat("2021-01-01T02:00:00"),
            process_id="test-process-id",
            pr_url="test-pr-url",
            pr_number=123,
        ),
    ]

    await event_store.append("test-process-id", *events)

    # When
    retrieved_events = await event_store.get("test-process-id")

    # Then
    assert retrieved_events == events


@pytest.mark.asyncio
async def test_get_issue_resolution_event_v2_with_resolution_settings(
    event_store: EventStore,
):
    # Given
    events: list[AnyDomainEvent] = [
        IssueResolutionRequested(
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            issue=IssueInfo(description="test issue"),
            user_id="test-user-id",
            agent=SupportedAgent.OPENAI_TOOLS,
            max_turns=69,
            ai_model=SupportedOpenAIModel.GPT5,
            ai_model_version="latest",
            execution_environment=ExecutionEnvironmentPreference.ENV_REQUIRED,
        ),
    ]

    await event_store.append("test-process-id", *events)

    # When
    retrieved_events = await event_store.get("test-process-id")

    # Then
    assert retrieved_events == events


@pytest.mark.asyncio
async def test_find_event_environment_configuration_provided(event_store: EventStore):
    # Given
    appended_event = EnvironmentConfigurationProvided(
        occurred_at=datetime.fromisoformat("2021-01-01T00:30:00"),
        process_id="test-process-id",
        environment_id="dev-environment-id-xyz",
        user_id="test-user-id",
        project_setup="apt update && apt install -y python3 \n pip install -e .'[dev]'",
        knowledge_base_id="knowledge-base-id",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
        },
        event_type=EnvironmentConfigurationProvided,
    )

    # Then
    assert events == [appended_event]


@pytest.mark.asyncio
async def test_find_event_issue_resolution_environment_prepared(
    event_store: EventStore,
):
    # Given
    appended_event = IssueResolutionEnvironmentPrepared(
        occurred_at=datetime.fromisoformat("2021-01-01T00:30:00"),
        process_id="test-process-id",
        environment_id="dev-environment-id-xyz",
        knowledge_base_id="knowledge-base-id",
        instance_id="instance-id-123",
    )
    await event_store.append("test-process-id", appended_event)

    # When
    events = await event_store.find(
        criteria={
            "knowledge_base_id": "knowledge-base-id",
        },
        event_type=IssueResolutionEnvironmentPrepared,
    )

    # Then
    assert events == [appended_event]
