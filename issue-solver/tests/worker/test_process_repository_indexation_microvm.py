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

from issue_solver.events.domain import RepositoryIndexationRequested
from issue_solver.cli.index_repository_command import IndexRepositoryCommandSettings
from issue_solver.git_operations.git_helper import CodeVersion, GitDiffFiles
from issue_solver.worker.dependencies import Dependencies
from issue_solver.worker.messages_processing import process_event_message
from tests.examples.happy_path_persona import BriceDeNice


@pytest.fixture
def microvm_client() -> Mock:
    return Mock(spec=MorphCloudClient)


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


@pytest.fixture
def repository_indexer():
    indexer = Mock()
    indexer.apply_delta.return_value = {"ok": 1}
    return indexer


def env_for_indexing(
    repo_url: str,
    access_token: str,
    knowledge_base_id: str,
    process_id: str,
    from_commit: str,
) -> str:
    settings = IndexRepositoryCommandSettings(
        repo_url=repo_url,
        access_token=access_token,
        knowledge_base_id=knowledge_base_id,
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
        from_commit_sha=from_commit,
        process_queue_url=None,
    )
    return settings.to_env_script()


@pytest.mark.asyncio
async def test_large_delta_indexation_runs_in_microvm_fire_and_forget(
    event_store,
    git_helper: Mock,
    time_under_control,
    microvm_client: Mock,
    worker_dependencies_with_microvm: Dependencies,
):
    # Given
    time_under_control.set_from_iso_format("2025-06-01T12:00:00")
    process_id = BriceDeNice.first_repo_integration_process_id()
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    await event_store.append(process_id, repo_connected)
    await event_store.append(process_id, repo_indexed)

    message = RepositoryIndexationRequested(
        knowledge_base_id=repo_connected.knowledge_base_id,
        user_id=repo_connected.user_id,
        process_id=process_id,
        occurred_at=time_under_control.now(),
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.pull_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.get_changed_files_commit.return_value = GitDiffFiles(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        added_files=[Path(f"src/new_{i}.py") for i in range(250)],
        deleted_files=[],
        modified_files=[],
        renamed_files=[],
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

    expected_env = env_for_indexing(
        repo_connected.url,
        repo_connected.access_token,
        repo_connected.knowledge_base_id,
        process_id,
        repo_indexed.commit_sha,
    )

    await process_event_message(message, worker_dependencies_with_microvm)

    # Then
    events = await event_store.get(process_id)
    assert events == [repo_connected, repo_indexed]
    microvm_client.snapshots.list.assert_called_once_with(metadata={"type": "base"})
    microvm_client.instances.start.assert_called_once_with(
        snapshot_id=base_snapshot.id, ttl_seconds=5400
    )
    script_sent = started_instance.exec.call_args.args[0]
    assert expected_env.strip() in script_sent
    assert "nohup runuser -u umans -- /bin/bash" in script_sent


@pytest.mark.asyncio
async def test_small_delta_runs_locally_even_with_microvm_available(
    event_store,
    git_helper: Mock,
    time_under_control,
    microvm_client: Mock,
    worker_dependencies_with_microvm: Dependencies,
    repository_indexer: Mock,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    await event_store.append(process_id, repo_connected)
    await event_store.append(process_id, repo_indexed)

    message = RepositoryIndexationRequested(
        knowledge_base_id=repo_connected.knowledge_base_id,
        user_id=repo_connected.user_id,
        process_id=process_id,
        occurred_at=time_under_control.now(),
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.pull_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.get_changed_files_commit.return_value = GitDiffFiles(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        added_files=[Path("src/new.py")],
        deleted_files=[],
        modified_files=[],
        renamed_files=[],
    )

    await process_event_message(message, worker_dependencies_with_microvm)

    # Then
    events = await event_store.get(process_id)
    assert len(events) == 3
    assert events[-1].commit_sha == "new-head-sha"
    microvm_client.instances.start.assert_not_called()
    repository_indexer.apply_delta.assert_called_once()


@pytest.mark.asyncio
async def test_large_delta_stays_local_when_microvm_unavailable(
    event_store, git_helper: Mock, time_under_control, repository_indexer
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    await event_store.append(process_id, repo_connected)
    await event_store.append(process_id, repo_indexed)

    message = RepositoryIndexationRequested(
        knowledge_base_id=repo_connected.knowledge_base_id,
        user_id=repo_connected.user_id,
        process_id=process_id,
        occurred_at=time_under_control.now(),
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.pull_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.get_changed_files_commit.return_value = GitDiffFiles(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        added_files=[Path(f"src/new_{i}.py") for i in range(250)],
        deleted_files=[],
        modified_files=[],
        renamed_files=[],
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

    await process_event_message(message, dependencies)

    # Then
    events = await event_store.get(process_id)
    assert len(events) == 3
    assert events[-1].commit_sha == "new-head-sha"
    repository_indexer.apply_delta.assert_called_once()


@pytest.mark.asyncio
async def test_offload_env_includes_routing_when_present(
    event_store,
    git_helper: Mock,
    time_under_control,
    microvm_client: Mock,
    worker_dependencies_with_microvm: Dependencies,
    monkeypatch,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    await event_store.append(process_id, repo_connected)
    await event_store.append(process_id, repo_indexed)

    message = RepositoryIndexationRequested(
        knowledge_base_id=repo_connected.knowledge_base_id,
        user_id=repo_connected.user_id,
        process_id=process_id,
        occurred_at=time_under_control.now(),
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.pull_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.get_changed_files_commit.return_value = GitDiffFiles(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        added_files=[Path(f"src/new_{i}.py") for i in range(250)],
        deleted_files=[],
        modified_files=[],
        renamed_files=[],
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

    captured_env = {}

    def fake_run_as_umans_with_env(env_body, command, global_setup_script=None, **_):
        captured_env["body"] = env_body
        captured_env["command"] = command
        return "script"

    monkeypatch.setenv("WEBHOOK_BASE_URL", "https://hooks.example.com")
    monkeypatch.setenv("PROCESS_QUEUE_URL", "https://sqs.example.com/queue")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.example")

    with patch(
        "issue_solver.worker.indexing.delta.run_as_umans_with_env",
        fake_run_as_umans_with_env,
    ):
        await process_event_message(message, worker_dependencies_with_microvm)

    # Then
    assert "WEBHOOK_BASE_URL='https://hooks.example.com'" in captured_env["body"]
    assert "PROCESS_QUEUE_URL" not in captured_env["body"]
    assert "OPENAI_API_KEY='sk-test-123'" in captured_env["body"]
    assert "OPENAI_BASE_URL='https://api.openai.example'" in captured_env["body"]
    assert captured_env["command"] == "cudu index-repository"
    started_instance.exec.assert_called_once_with("script")


@pytest.mark.asyncio
async def test_access_token_missing_skips_offload(
    event_store,
    git_helper: Mock,
    time_under_control,
    microvm_client: Mock,
    worker_dependencies_with_microvm: Dependencies,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    await event_store.append(process_id, repo_connected)
    await event_store.append(process_id, repo_indexed)

    message = RepositoryIndexationRequested(
        knowledge_base_id=repo_connected.knowledge_base_id,
        user_id=repo_connected.user_id,
        process_id=process_id,
        occurred_at=time_under_control.now(),
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.pull_repository.return_value = CodeVersion(
        branch="main", commit_sha="new-head-sha"
    )
    git_helper.get_changed_files_commit.return_value = GitDiffFiles(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        added_files=[Path(f"src/new_{i}.py") for i in range(250)],
        deleted_files=[],
        modified_files=[],
        renamed_files=[],
    )

    base_snapshot = Mock(spec=Snapshot)
    base_snapshot.id = "base-snapshot-id"
    base_snapshot.status = SnapshotStatus.READY
    microvm_client.snapshots.list.return_value = [base_snapshot]

    with patch(
        "issue_solver.worker.indexing.delta.get_access_token",
        AsyncMock(return_value=None),
    ):
        await process_event_message(message, worker_dependencies_with_microvm)

    # Then
    events = await event_store.get(process_id)
    assert events == [repo_connected, repo_indexed]
    microvm_client.instances.start.assert_not_called()


def to_script(command: str, dotenv_settings: str) -> str:
    return f"""
set -Eeuo pipefail
umask 0077

trap 'rm -f "/home/umans/.cudu_env" "/home/umans/.cudu_run.sh"' EXIT

# 1) write .env literally
cat > "/home/umans/.cudu_env" <<'ENV'
{dotenv_settings.strip()}
ENV
chown umans:umans "/home/umans/.cudu_env"
chmod 600 "/home/umans/.cudu_env"

# 2) write the exec script literally (owned by umans)
cat > "/home/umans/.cudu_run.sh" <<'SH'
#!/bin/bash
set -Eeuo pipefail
set -a
. "/home/umans/.cudu_env"
set +a

# --- pick a safe working directory so .env is readable ---
if [ -n "${{REPO_PATH:-}}" ] && [ "${{REPO_PATH:0:1}}" = "/" ]; then
  mkdir -p "${{REPO_PATH}}"
  cd "${{REPO_PATH}}" || cd "$HOME"
else
  cd "$HOME"
fi

# ensure PATH is sane for user invocations
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# quick sanity (leave for now; remove once stable)
echo "PWD=$(pwd)"; echo "PATH=$PATH"; command -v cudu >/dev/null || {{ echo "cudu not found" >&2; exit 127; }}

exec {command} | tee -a /home/umans/.cudu_run.log
SH
chown umans:umans "/home/umans/.cudu_run.sh"
chmod 700 "/home/umans/.cudu_run.sh"

# 3) run as umans without -c or -l
runuser -u umans -- /bin/bash "/home/umans/.cudu_run.sh"
"""


def to_script_background(command: str, dotenv_settings: str) -> str:
    return f"""
set -Eeuo pipefail
umask 0077

# 1) write .env literally
cat > "/home/umans/.cudu_env" <<'ENV'
{dotenv_settings.strip()}
ENV
chown umans:umans "/home/umans/.cudu_env"
chmod 600 "/home/umans/.cudu_env"

# 2) write the exec script literally (owned by umans)
cat > "/home/umans/.cudu_run.sh" <<'SH'
#!/bin/bash
set -Eeuo pipefail
set -a
. "/home/umans/.cudu_env"
set +a

# --- pick a safe working directory so .env is readable ---
if [ -n "${{REPO_PATH:-}}" ] && [ "${{REPO_PATH:0:1}}" = "/" ]; then
  mkdir -p "${{REPO_PATH}}"
  cd "${{REPO_PATH}}" || cd "$HOME"
else
  cd "$HOME"
fi

# ensure PATH is sane for user invocations
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# quick sanity (leave for now; remove once stable)
echo "PWD=$(pwd)"; echo "PATH=$PATH"; command -v cudu >/dev/null || {{ echo "cudu not found" >&2; exit 127; }}

exec {command} | tee -a /home/umans/.cudu_run.log
SH
chown umans:umans "/home/umans/.cudu_run.sh"
chmod 700 "/home/umans/.cudu_run.sh"

# 3) run as umans without -c or -l
nohup runuser -u umans -- /bin/bash -lc 'set -Eeuo pipefail; set -a; . "/home/umans/.cudu_env"; set +a; if [ -n "${{REPO_PATH:-}}" ] && [ "${{REPO_PATH:0:1}}" = "/" ]; then mkdir -p "${{REPO_PATH}}"; cd "${{REPO_PATH}}" || cd "$HOME"; else cd "$HOME"; fi; export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"; echo "PWD=$(pwd)"; echo "PATH=$PATH"; command -v cudu >/dev/null || {{ echo "cudu not found" >&2; exit 127; }}; exec {command}' >> /home/umans/.cudu_run.log 2>&1 < /dev/null & echo $! > /home/umans/.cudu_run.pid
"""
