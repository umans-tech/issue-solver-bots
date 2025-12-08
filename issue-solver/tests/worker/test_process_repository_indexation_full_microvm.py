from pathlib import Path
from typing import Any, Callable, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
from morphcloud.api import (
    Instance,
    InstanceExecResponse,
    MorphCloudClient,
    Snapshot,
    SnapshotStatus,
)

from issue_solver.events.domain import CodeRepositoryIndexed
from issue_solver.cli.index_repository_command import IndexRepositoryCommandSettings
from issue_solver.git_operations.git_helper import CodeVersion
from issue_solver.worker.dependencies import Dependencies
from issue_solver.worker.messages_processing import process_event_message
from tests.examples.happy_path_persona import BriceDeNice


@pytest.fixture
def microvm_client() -> Mock:
    return Mock(spec=MorphCloudClient)


@pytest.fixture
def repository_indexer() -> Mock:
    indexer = Mock()
    indexer.upload_full_repository.return_value = {"ok": 1}
    return indexer


@pytest.fixture
def worker_dependencies_with_microvm(
    event_store, time_under_control, microvm_client, git_helper, repository_indexer
) -> Dependencies:
    return Dependencies(
        event_store,
        Mock(),
        AsyncMock(),
        Mock(),
        time_under_control,
        microvm_client=microvm_client,
        is_dev_environment_service_enabled=True,
        git_helper_factory=cast(
            Callable[[Any, Any | None], Any],
            lambda settings, validation_service=None: git_helper,
        ),
        repository_indexer=repository_indexer,
    )


def env_for_full_indexing(
    repo_url: str,
    access_token: str,
    knowledge_base_id: str,
    process_id: str,
) -> str:
    settings = IndexRepositoryCommandSettings(
        repo_url=repo_url,
        access_token=access_token,
        knowledge_base_id=knowledge_base_id,
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
        process_queue_url=None,
    )
    return settings.to_env_script()


@pytest.mark.asyncio
async def test_full_indexation_offloads_to_microvm_fire_and_forget(
    event_store,
    git_helper: Mock,
    time_under_control,
    microvm_client: Mock,
    worker_dependencies_with_microvm: Dependencies,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    message = BriceDeNice.got_his_first_repo_connected()

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )

    base_snapshot = Mock(spec=Snapshot)
    base_snapshot.id = "base-snapshot-id"
    base_snapshot.status = SnapshotStatus.READY
    microvm_client.snapshots.list.return_value = [base_snapshot]
    started_instance = Mock(spec=Instance)
    started_instance.id = "instance-id"
    started_instance.exec.return_value = InstanceExecResponse(
        exit_code=0, stdout="queued", stderr=""
    )
    microvm_client.instances.start.return_value = started_instance

    expected_env = env_for_full_indexing(
        repo_url=message.url,
        access_token=message.access_token,
        knowledge_base_id=message.knowledge_base_id,
        process_id=process_id,
    )

    with patch(
        "issue_solver.worker.indexing.full.run_as_umans_with_env"
    ) as run_as_umans:
        run_as_umans.side_effect = lambda *args, **kwargs: args[0]
        # When
        await process_event_message(message, worker_dependencies_with_microvm)

    # Then
    events = await event_store.get(process_id)
    assert events == []
    microvm_client.snapshots.list.assert_called_once_with(metadata={"type": "base"})
    microvm_client.instances.start.assert_called_once_with(
        snapshot_id=base_snapshot.id, ttl_seconds=5400
    )
    run_as_umans.assert_called_once()
    env_body_arg, command_arg = run_as_umans.call_args.args[:2]
    assert "WEBHOOK_BASE_URL" not in env_body_arg
    assert env_body_arg.strip() == expected_env.strip()
    assert command_arg == "cudu index-repository"
    started_instance.exec.assert_called_once()


@pytest.mark.asyncio
async def test_full_indexation_runs_locally_when_microvm_unavailable(
    event_store, git_helper: Mock, time_under_control, repository_indexer: Mock
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    message = BriceDeNice.got_his_first_repo_connected()

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )

    dependencies = Dependencies(
        event_store,
        Mock(),
        AsyncMock(),
        Mock(),
        time_under_control,
        microvm_client=None,
        is_dev_environment_service_enabled=True,
        git_helper_factory=cast(
            Callable[[Any, Any | None], Any],
            lambda settings, validation_service=None: git_helper,
        ),
        repository_indexer=repository_indexer,
    )

    # When
    await process_event_message(message, dependencies)

    # Then
    events = await event_store.get(process_id)
    assert any(isinstance(e, CodeRepositoryIndexed) for e in events)
    repository_indexer.upload_full_repository.assert_called_once_with(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        vector_store_id=message.knowledge_base_id,
    )
