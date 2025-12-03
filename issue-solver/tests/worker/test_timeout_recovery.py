from datetime import datetime, timedelta

import pytest

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    CodeRepositoryIntegrationFailed,
    IssueResolutionRequested,
)
from issue_solver.issues.issue import IssueInfo
from issue_solver.worker.indexing.timeout_recovery import recover_timed_out_indexing


@pytest.mark.asyncio
async def test_recover_marks_stale_unfinished_repo_as_failed(
    event_store, worker_dependencies, time_under_control
):
    # Given
    time_under_control.set(datetime.fromisoformat("2022-01-01T10:00:00"))
    stale_started_at = time_under_control.now() - timedelta(hours=3)
    stuck_repo = CodeRepositoryConnected(
        url="https://github.com/example/stuck.git",
        access_token="token",
        user_id="user-1",
        space_id="space-1",
        knowledge_base_id="kb-stale",
        process_id="process-stale",
        occurred_at=stale_started_at,
    )
    await event_store.append(stuck_repo.process_id, stuck_repo)

    # When
    await recover_timed_out_indexing(worker_dependencies)

    # Then
    events = await event_store.get(stuck_repo.process_id)
    assert len(events) == 2
    assert isinstance(events[-1], CodeRepositoryIntegrationFailed)
    assert "timeout" in events[-1].error_type


@pytest.mark.asyncio
async def test_recover_skips_repos_that_already_finished(
    event_store, worker_dependencies, time_under_control
):
    # Given
    time_under_control.set(datetime.fromisoformat("2022-01-01T10:00:00"))
    long_ago = time_under_control.now() - timedelta(hours=4)
    finished_repo = CodeRepositoryConnected(
        url="https://github.com/example/finished.git",
        access_token="token",
        user_id="user-2",
        space_id="space-2",
        knowledge_base_id="kb-finished",
        process_id="process-finished",
        occurred_at=long_ago,
    )
    already_indexed = CodeRepositoryIndexed(
        branch="main",
        commit_sha="abc123",
        stats={},
        knowledge_base_id=finished_repo.knowledge_base_id,
        process_id=finished_repo.process_id,
        occurred_at=long_ago + timedelta(minutes=10),
    )
    await event_store.append(finished_repo.process_id, finished_repo, already_indexed)

    # When
    await recover_timed_out_indexing(worker_dependencies)

    # Then
    events = await event_store.get(finished_repo.process_id)
    assert len(events) == 2
    assert isinstance(events[-1], CodeRepositoryIndexed)


@pytest.mark.asyncio
async def test_recover_skips_recent_in_progress_repo(
    event_store, worker_dependencies, time_under_control
):
    # Given
    time_under_control.set(datetime.fromisoformat("2022-01-01T10:00:00"))
    recent_started_at = time_under_control.now() - timedelta(minutes=30)
    recent_repo = CodeRepositoryConnected(
        url="https://github.com/example/recent.git",
        access_token="token",
        user_id="user-3",
        space_id="space-3",
        knowledge_base_id="kb-recent",
        process_id="process-recent",
        occurred_at=recent_started_at,
    )
    await event_store.append(recent_repo.process_id, recent_repo)

    # When
    await recover_timed_out_indexing(worker_dependencies)

    # Then
    events = await event_store.get(recent_repo.process_id)
    assert len(events) == 1
    assert isinstance(events[-1], CodeRepositoryConnected)


@pytest.mark.asyncio
async def test_recover_only_marks_repo_processes_not_other_process_types(
    event_store, worker_dependencies, time_under_control
):
    # Given
    time_under_control.set(datetime.fromisoformat("2022-01-01T10:00:00"))
    stale_repo = CodeRepositoryConnected(
        url="https://github.com/example/stale.git",
        access_token="token",
        user_id="user-4",
        space_id="space-4",
        knowledge_base_id="kb-stale-2",
        process_id="process-stale-2",
        occurred_at=time_under_control.now() - timedelta(hours=3),
    )
    unrelated_issue = IssueResolutionRequested(
        knowledge_base_id="kb-stale-2",
        issue=IssueInfo(description="d", title="t"),
        process_id="issue-process",
        occurred_at=time_under_control.now() - timedelta(hours=3),
    )
    await event_store.append(stale_repo.process_id, stale_repo)
    await event_store.append(unrelated_issue.process_id, unrelated_issue)

    # When
    await recover_timed_out_indexing(worker_dependencies)

    # Then
    repo_events = await event_store.get(stale_repo.process_id)
    assert isinstance(repo_events[-1], CodeRepositoryIntegrationFailed)

    issue_events = await event_store.get(unrelated_issue.process_id)
    assert len(issue_events) == 1
    assert isinstance(issue_events[-1], IssueResolutionRequested)


@pytest.mark.asyncio
async def test_recover_is_idempotent_when_failure_already_emitted(
    event_store, worker_dependencies, time_under_control
):
    # Given
    time_under_control.set(datetime.fromisoformat("2022-01-01T10:00:00"))
    started_at = time_under_control.now() - timedelta(hours=3)
    repo = CodeRepositoryConnected(
        url="https://github.com/example/already-failed.git",
        access_token="token",
        user_id="user-5",
        space_id="space-5",
        knowledge_base_id="kb-failed",
        process_id="process-failed",
        occurred_at=started_at,
    )
    first_failure = CodeRepositoryIntegrationFailed(
        url=repo.url,
        error_type="timeout",
        error_message="timeout",
        knowledge_base_id=repo.knowledge_base_id,
        process_id=repo.process_id,
        occurred_at=started_at + timedelta(minutes=5),
    )
    await event_store.append(repo.process_id, repo, first_failure)

    # When
    await recover_timed_out_indexing(worker_dependencies)

    # Then
    events = await event_store.get(repo.process_id)
    assert len(events) == 2
    assert events[-1] is first_failure


@pytest.mark.asyncio
async def test_recover_only_marks_old_unfinished_repos_among_mixed_processes(
    event_store, worker_dependencies, time_under_control
):
    # Given
    time_under_control.set(datetime.fromisoformat("2022-01-01T10:00:00"))
    stale_repo = CodeRepositoryConnected(
        url="https://github.com/example/stale-mixed.git",
        access_token="token",
        user_id="user-6",
        space_id="space-6",
        knowledge_base_id="kb-stale-mixed",
        process_id="process-stale-mixed",
        occurred_at=time_under_control.now() - timedelta(hours=3),
    )
    recent_repo = CodeRepositoryConnected(
        url="https://github.com/example/recent-mixed.git",
        access_token="token",
        user_id="user-7",
        space_id="space-7",
        knowledge_base_id="kb-recent-mixed",
        process_id="process-recent-mixed",
        occurred_at=time_under_control.now() - timedelta(minutes=45),
    )
    finished_repo = CodeRepositoryConnected(
        url="https://github.com/example/finished-mixed.git",
        access_token="token",
        user_id="user-8",
        space_id="space-8",
        knowledge_base_id="kb-finished-mixed",
        process_id="process-finished-mixed",
        occurred_at=time_under_control.now() - timedelta(hours=4),
    )
    finished_event = CodeRepositoryIndexed(
        branch="main",
        commit_sha="def456",
        stats={},
        knowledge_base_id=finished_repo.knowledge_base_id,
        process_id=finished_repo.process_id,
        occurred_at=finished_repo.occurred_at + timedelta(minutes=20),
    )
    await event_store.append(stale_repo.process_id, stale_repo)
    await event_store.append(recent_repo.process_id, recent_repo)
    await event_store.append(finished_repo.process_id, finished_repo, finished_event)

    # When
    await recover_timed_out_indexing(worker_dependencies)

    # Then
    stale_events = await event_store.get(stale_repo.process_id)
    assert isinstance(stale_events[-1], CodeRepositoryIntegrationFailed)

    recent_events = await event_store.get(recent_repo.process_id)
    assert isinstance(recent_events[-1], CodeRepositoryConnected)

    finished_events = await event_store.get(finished_repo.process_id)
    assert isinstance(finished_events[-1], CodeRepositoryIndexed)
