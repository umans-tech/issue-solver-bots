from pathlib import Path
from unittest.mock import Mock

import pytest

from issue_solver.cli.index_repository_command import (
    IndexRepositoryCommandSettings,
    IndexRepositoryDependencies,
    main as run_index_repository,
)
from issue_solver.indexing.repository_indexer import RepositoryIndexer
from issue_solver.events.domain import (
    CodeRepositoryIndexed,
    CodeRepositoryIntegrationFailed,
)
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.git_operations.git_helper import (
    CodeVersion,
    GitDiffFiles,
    GitHelper,
    GitValidationError,
)
from datetime import datetime, timezone

from issue_solver.clock import Clock
from tests.controllable_clock import ControllableClock
from tests.examples.happy_path_persona import BriceDeNice


@pytest.fixture
def event_store() -> InMemoryEventStore:
    return InMemoryEventStore()


@pytest.fixture
def git_helper() -> Mock:
    return Mock(spec=GitHelper)


@pytest.fixture
def repository_indexer() -> Mock:
    return Mock(spec=RepositoryIndexer)


@pytest.fixture
def clock() -> Clock:
    return ControllableClock(datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def index_repo_deps(
    event_store: InMemoryEventStore,
    git_helper: Mock,
    repository_indexer: Mock,
    clock: Clock,
) -> IndexRepositoryDependencies:
    return IndexRepositoryDependencies(
        event_store=event_store,
        git_helper=git_helper,
        indexer=repository_indexer,
        clock=clock,
    )


@pytest.mark.asyncio
async def test_full_mode_shallow_clone_and_emits_indexed_event(
    event_store: InMemoryEventStore,
    git_helper: Mock,
    repository_indexer: Mock,
    index_repo_deps: IndexRepositoryDependencies,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    settings = IndexRepositoryCommandSettings(
        repo_url="https://github.com/umans-tech/issue-solver-bots.git",
        access_token="ghp_dummy",
        knowledge_base_id="kb-001",
        webhook_base_url="https://api.example.umans.ai",
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="abc123"
    )
    stats = {"total_files": 3, "successful_uploads": 3}
    repository_indexer.upload_full_repository.return_value = stats

    # When
    await run_index_repository(settings, index_repo_deps)

    # Then
    events = await event_store.get(process_id)
    assert any(isinstance(event, CodeRepositoryIndexed) for event in events)
    indexed_event = next(
        event for event in events if isinstance(event, CodeRepositoryIndexed)
    )
    assert indexed_event.branch == "main"
    assert indexed_event.commit_sha == "abc123"
    assert indexed_event.stats == stats
    git_helper.clone_repository.assert_called_once_with(
        Path(f"/tmp/repo/{process_id}"), depth=1
    )
    repository_indexer.upload_full_repository.assert_called_once_with(
        Path(f"/tmp/repo/{process_id}"), "kb-001"
    )


@pytest.mark.asyncio
async def test_delta_mode_indexes_diff_and_unindexes_obsolete(
    event_store: InMemoryEventStore,
    git_helper: Mock,
    repository_indexer: Mock,
    index_repo_deps: IndexRepositoryDependencies,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    settings = IndexRepositoryCommandSettings(
        repo_url="https://github.com/umans-tech/issue-solver-bots.git",
        access_token="ghp_dummy",
        knowledge_base_id="kb-001",
        webhook_base_url="https://api.example.umans.ai",
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
        from_commit_sha="deadbeef",
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="cafebabe"
    )
    git_helper.pull_repository.return_value = CodeVersion(
        branch="main", commit_sha="cafebabe"
    )
    git_helper.get_changed_files_commit.return_value = GitDiffFiles(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        added_files=[Path("src/new.py")],
        deleted_files=[Path("src/old.py")],
        modified_files=[Path("src/changed.py")],
        renamed_files=[],
    )

    delta_stats = {
        "new_indexed_files": {"successful_uploads": 2},
        "obsolete_files": {"successful_search": 1},
        "unindexed_files": {"successful_unindexing": 1},
    }
    repository_indexer.apply_delta.return_value = delta_stats

    # When
    await run_index_repository(settings, index_repo_deps)

    # Then
    events = await event_store.get(process_id)
    assert any(isinstance(event, CodeRepositoryIndexed) for event in events)
    indexed_event = next(
        event for event in events if isinstance(event, CodeRepositoryIndexed)
    )
    assert indexed_event.commit_sha == "cafebabe"
    assert indexed_event.stats == delta_stats
    git_helper.get_changed_files_commit.assert_called_once_with(
        Path(f"/tmp/repo/{process_id}"), "deadbeef"
    )
    repository_indexer.apply_delta.assert_called_once()


@pytest.mark.asyncio
async def test_auto_delta_uses_last_indexed_commit_when_missing_from_commit(
    index_repo_deps: IndexRepositoryDependencies,
    git_helper: Mock,
    repository_indexer: Mock,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    last_commit = "prev123"
    await index_repo_deps.event_store.append(
        process_id,
        CodeRepositoryIndexed(
            branch="main",
            commit_sha=last_commit,
            stats={"files_indexed": 10},
            knowledge_base_id="kb-001",
            process_id=process_id,
            occurred_at=index_repo_deps.clock.now(),
        ),
    )

    settings = IndexRepositoryCommandSettings(
        repo_url="https://github.com/umans-tech/issue-solver-bots.git",
        access_token="ghp_dummy",
        knowledge_base_id="kb-001",
        webhook_base_url="https://api.example.umans.ai",
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="newhead"
    )
    git_helper.get_changed_files_commit.return_value = GitDiffFiles(
        repo_path=settings.repo_path,
        added_files=[Path("src/new.py")],
        deleted_files=[],
        modified_files=[],
        renamed_files=[],
    )
    repository_indexer.apply_delta.return_value = {
        "new_indexed_files": {"successful_uploads": 1}
    }

    # When
    await run_index_repository(settings, index_repo_deps)

    # Then
    git_helper.clone_repository.assert_called_once_with(settings.repo_path, depth=None)
    git_helper.get_changed_files_commit.assert_called_once_with(
        settings.repo_path, last_commit
    )
    repository_indexer.apply_delta.assert_called_once()
    events = await index_repo_deps.event_store.get(process_id)
    assert any(
        isinstance(event, CodeRepositoryIndexed) and event.commit_sha == "newhead"
        for event in events
    )


@pytest.mark.asyncio
async def test_explicit_from_commit_overrides_last_indexed(
    index_repo_deps: IndexRepositoryDependencies,
    git_helper: Mock,
    repository_indexer: Mock,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    await index_repo_deps.event_store.append(
        process_id,
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="prev123",
            stats={"files_indexed": 10},
            knowledge_base_id="kb-001",
            process_id=process_id,
            occurred_at=index_repo_deps.clock.now(),
        ),
    )

    settings = IndexRepositoryCommandSettings(
        repo_url="https://github.com/umans-tech/issue-solver-bots.git",
        access_token="ghp_dummy",
        knowledge_base_id="kb-001",
        webhook_base_url="https://api.example.umans.ai",
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
        from_commit_sha="explicit123",
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="newhead"
    )
    git_helper.get_changed_files_commit.return_value = GitDiffFiles(
        repo_path=settings.repo_path,
        added_files=[Path("src/new.py")],
        deleted_files=[],
        modified_files=[],
        renamed_files=[],
    )
    repository_indexer.apply_delta.return_value = {
        "new_indexed_files": {"successful_uploads": 1}
    }

    # When
    await run_index_repository(settings, index_repo_deps)

    # Then
    git_helper.get_changed_files_commit.assert_called_once_with(
        settings.repo_path, "explicit123"
    )
    repository_indexer.apply_delta.assert_called_once()


@pytest.mark.asyncio
async def test_git_validation_error_emits_integration_failed(
    event_store: InMemoryEventStore,
    git_helper: Mock,
    repository_indexer: Mock,
    index_repo_deps: IndexRepositoryDependencies,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    settings = IndexRepositoryCommandSettings(
        repo_url="https://github.com/umans-tech/issue-solver-bots.git",
        access_token="ghp_dummy",
        knowledge_base_id="kb-001",
        webhook_base_url="https://api.example.umans.ai",
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
    )

    git_helper.clone_repository.side_effect = GitValidationError(
        "Authentication failed", "authentication_failed", status_code=401
    )

    # When
    with pytest.raises(GitValidationError):
        await run_index_repository(settings, index_repo_deps)

    # Then
    events = await event_store.get(process_id)
    assert any(isinstance(event, CodeRepositoryIntegrationFailed) for event in events)
    failure = next(
        event for event in events if isinstance(event, CodeRepositoryIntegrationFailed)
    )
    assert failure.error_type == "authentication_failed"


@pytest.mark.asyncio
async def test_unexpected_error_emits_generic_integration_failed(
    event_store: InMemoryEventStore,
    git_helper: Mock,
    repository_indexer: Mock,
    index_repo_deps: IndexRepositoryDependencies,
):
    # Given
    process_id = BriceDeNice.first_repo_integration_process_id()
    settings = IndexRepositoryCommandSettings(
        repo_url="https://github.com/umans-tech/issue-solver-bots.git",
        access_token="ghp_dummy",
        knowledge_base_id="kb-001",
        webhook_base_url="https://api.example.umans.ai",
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
    )

    git_helper.clone_repository.return_value = CodeVersion(
        branch="main", commit_sha="abc123"
    )

    repository_indexer.upload_full_repository.side_effect = RuntimeError("boom")

    # When
    with pytest.raises(RuntimeError):
        await run_index_repository(settings, index_repo_deps)

    # Then
    events = await event_store.get(process_id)
    assert any(isinstance(event, CodeRepositoryIntegrationFailed) for event in events)
    failure = next(
        event for event in events if isinstance(event, CodeRepositoryIntegrationFailed)
    )
    assert failure.error_type == "unexpected_error"
