from datetime import datetime, timedelta

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryTokenRotated,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    IssueResolutionRequested,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    IssueResolutionFailed,
    CodeRepositoryIntegrationFailed,
    DocumentationPromptsDefined,
    DocumentationPromptsRemoved,
    DocumentationGenerationRequested,
    DocumentationGenerationStarted,
    DocumentationGenerationCompleted,
    DocumentationGenerationFailed,
)
from issue_solver.issues.issue import IssueInfo
from issue_solver.webapi.routers import processes as processes_router
from issue_solver.webapi.routers.processes import ProcessTimelineView
from tests.examples.happy_path_persona import BriceDeNice


def test_status_should_be_connected_latest_event_is_connected():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        )
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "connected"


def test_status_should_be_indexed_if_latest_event_is_indexed():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexed"


def test_status_should_be_indexing_if_the_latest_event_is_indexation_requested():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
        RepositoryIndexationRequested(
            occurred_at=datetime.fromisoformat("2025-01-01T02:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            user_id="test-user-id",
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexing"


def test_status_should_be_indexed_if_the_latest_event_is_indexed_after_indexation_requested():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
        RepositoryIndexationRequested(
            occurred_at=datetime.fromisoformat("2025-01-01T02:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            user_id="test-user-id",
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T03:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexed"


def test_status_should_be_started_when_the_latest_event_is_issue_resolution_in_progress():
    # Given
    history = [
        IssueResolutionRequested(
            knowledge_base_id="knowledge-base-id",
            issue=IssueInfo(
                description="test-issue-description",
                title="test-issue-title",
            ),
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        IssueResolutionStarted(
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
    ]
    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.type == "issue_resolution"
    assert process_timeline_view.status == "in_progress"


def test_status_should_be_completed_when_the_latest_event_is_issue_resolution_completed():
    # Given
    history = [
        IssueResolutionRequested(
            knowledge_base_id="knowledge-base-id",
            issue=IssueInfo(
                description="test-issue-description",
                title="test-issue-title",
            ),
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        IssueResolutionStarted(
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
        IssueResolutionCompleted(
            pr_url="test-pr-url",
            pr_number=123,
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T02:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.type == "issue_resolution"
    assert process_timeline_view.status == "completed"


def test_status_should_be_failed_when_the_latest_event_is_issue_resolution_failed():
    # Given
    history = [
        IssueResolutionRequested(
            knowledge_base_id="knowledge-base-id",
            issue=IssueInfo(
                description="test-issue-description",
                title="test-issue-title",
            ),
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        IssueResolutionStarted(
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
        IssueResolutionFailed(
            reason="test-reason",
            error_message="test-error-message",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T02:00:00"),
        ),
    ]
    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.type == "issue_resolution"
    assert process_timeline_view.status == "failed"


def test_auto_documentation_process_should_report_configured_status():
    # Given
    history = [
        DocumentationPromptsDefined(
            knowledge_base_id="kb-123",
            user_id="doc-bot@example.com",
            docs_prompts={"glossary": "Document the glossary"},
            process_id="doc-process-123",
            occurred_at=datetime.fromisoformat("2025-11-02T10:00:00"),
        )
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="doc-process-123", events=history
    )

    # Then
    assert process_timeline_view.type == "docs_setup"
    assert process_timeline_view.status == "configured"


def test_auto_documentation_process_should_report_removed_status():
    # Given
    history = [
        DocumentationPromptsDefined(
            knowledge_base_id="kb-123",
            user_id="doc-bot@example.com",
            docs_prompts={"glossary": "Document the glossary"},
            process_id="doc-process-123",
            occurred_at=datetime.fromisoformat("2025-11-02T10:00:00"),
        ),
        DocumentationPromptsRemoved(
            knowledge_base_id="kb-123",
            user_id="doc-bot@example.com",
            prompt_ids={"glossary"},
            process_id="doc-process-123",
            occurred_at=datetime.fromisoformat("2025-11-02T11:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="doc-process-123", events=history
    )

    # Then
    assert process_timeline_view.type == "docs_setup"
    assert process_timeline_view.status == "removed"


def test_doc_generation_process_should_report_requested_status():
    run_id = "generation-run-001"
    child_process_id = "doc-child-001"
    history = [
        DocumentationGenerationRequested(
            knowledge_base_id="kb-123",
            prompt_id="overview",
            prompt_description="Generate overview",
            code_version="commit-sha",
            run_id=run_id,
            process_id=child_process_id,
            occurred_at=datetime.fromisoformat("2025-11-02T12:00:00"),
        )
    ]

    process_timeline_view = ProcessTimelineView.create_from(
        process_id=child_process_id, events=history
    )

    assert process_timeline_view.type == "docs_generation"
    assert process_timeline_view.status == "requested"
    assert process_timeline_view.run_id == run_id


def test_doc_generation_process_should_report_in_progress_status():
    run_id = "generation-run-001"
    child_process_id = "doc-child-001"
    history = [
        DocumentationGenerationRequested(
            knowledge_base_id="kb-123",
            prompt_id="overview",
            prompt_description="Generate overview",
            code_version="commit-sha",
            run_id=run_id,
            process_id=child_process_id,
            occurred_at=datetime.fromisoformat("2025-11-02T12:00:00"),
        ),
        DocumentationGenerationStarted(
            knowledge_base_id="kb-123",
            prompt_id="overview",
            code_version="commit-sha",
            run_id=run_id,
            process_id=child_process_id,
            occurred_at=datetime.fromisoformat("2025-11-02T12:00:30"),
        ),
    ]

    process_timeline_view = ProcessTimelineView.create_from(
        process_id=child_process_id, events=history
    )

    assert process_timeline_view.type == "docs_generation"
    assert process_timeline_view.status == "in_progress"
    assert process_timeline_view.run_id == run_id


def test_doc_generation_process_should_report_completed_status():
    run_id = "generation-run-001"
    child_process_id = "doc-child-001"
    history = [
        DocumentationGenerationRequested(
            knowledge_base_id="kb-123",
            prompt_id="overview",
            prompt_description="Generate overview",
            code_version="commit-sha",
            run_id=run_id,
            process_id=child_process_id,
            occurred_at=datetime.fromisoformat("2025-11-02T12:00:00"),
        ),
        DocumentationGenerationStarted(
            knowledge_base_id="kb-123",
            prompt_id="overview",
            code_version="commit-sha",
            run_id=run_id,
            process_id=child_process_id,
            occurred_at=datetime.fromisoformat("2025-11-02T12:00:30"),
        ),
        DocumentationGenerationCompleted(
            knowledge_base_id="kb-123",
            prompt_id="overview",
            code_version="commit-sha",
            run_id=run_id,
            generated_documents=["overview.md"],
            process_id=child_process_id,
            occurred_at=datetime.fromisoformat("2025-11-02T12:05:00"),
        ),
    ]

    process_timeline_view = ProcessTimelineView.create_from(
        process_id=child_process_id, events=history
    )

    assert process_timeline_view.type == "docs_generation"
    assert process_timeline_view.status == "completed"
    assert process_timeline_view.run_id == run_id


def test_doc_generation_process_should_report_failed_status():
    run_id = "generation-run-001"
    child_process_id = "doc-child-001"
    history = [
        DocumentationGenerationRequested(
            knowledge_base_id="kb-123",
            prompt_id="overview",
            prompt_description="Generate overview",
            code_version="commit-sha",
            run_id=run_id,
            process_id=child_process_id,
            occurred_at=datetime.fromisoformat("2025-11-02T12:00:00"),
        ),
        DocumentationGenerationFailed(
            knowledge_base_id="kb-123",
            prompt_id="overview",
            code_version="commit-sha",
            run_id=run_id,
            error_message="boom",
            process_id=child_process_id,
            occurred_at=datetime.fromisoformat("2025-11-02T12:05:00"),
        ),
    ]

    process_timeline_view = ProcessTimelineView.create_from(
        process_id=child_process_id, events=history
    )

    assert process_timeline_view.type == "docs_generation"
    assert process_timeline_view.status == "failed"
    assert process_timeline_view.run_id == run_id


def test_apply_filters_should_filter_by_run_id():
    processes = [
        ProcessTimelineView(
            id="doc-run-1",
            type="docs_generation",
            status="completed",
            run_id="run-123",
            events=[],
        ),
        ProcessTimelineView(
            id="doc-run-2",
            type="docs_generation",
            status="completed",
            run_id="run-456",
            events=[],
        ),
    ]

    filtered = processes_router._apply_filters(
        processes, "docs_generation", None, "run-123"
    )

    assert [p.id for p in filtered] == ["doc-run-1"]


def test_status_should_remain_connected_after_token_rotation():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        ),
        CodeRepositoryTokenRotated(
            knowledge_base_id="knowledge-base-id",
            new_access_token="new-test-token",
            user_id="test-user-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "connected"


def test_status_should_remain_indexed_after_token_rotation():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
        ),
        CodeRepositoryTokenRotated(
            knowledge_base_id="knowledge-base-id",
            new_access_token="new-test-token",
            user_id="test-user-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T02:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexed"


def test_status_should_remain_indexing_after_token_rotation():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
        ),
        RepositoryIndexationRequested(
            occurred_at=datetime.fromisoformat("2021-01-01T02:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            user_id="test-user-id",
        ),
        CodeRepositoryTokenRotated(
            knowledge_base_id="knowledge-base-id",
            new_access_token="new-test-token",
            user_id="test-user-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T03:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexing"


def test_status_should_be_unknown_when_only_token_rotation_events():
    # Given - Only token rotation events (edge case)
    history = [
        CodeRepositoryTokenRotated(
            knowledge_base_id="knowledge-base-id",
            new_access_token="new-test-token",
            user_id="test-user-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "unknown"


def test_status_should_be_failed_when_latest_event_is_code_repo_integration_failed_among_others():
    # Given
    repo_connected = BriceDeNice.got_his_first_repo_connected()

    history = [
        repo_connected,
        CodeRepositoryIntegrationFailed(
            url="https://github.com/brice/nice-repo.git",
            error_type="permission_denied",
            error_message="test-error-message",
            knowledge_base_id="brice-user-001",
            process_id=BriceDeNice.first_repo_integration_process_id(),
            occurred_at=repo_connected.occurred_at + timedelta(seconds=2),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id=BriceDeNice.first_repo_integration_process_id(), events=history
    )
    # Then
    assert process_timeline_view.status == "failed"
    assert process_timeline_view.type == "code_repository_integration"


def test_should_be_configuring_when_latest_event_is_env_configuration_provided():
    # Given
    configuration_provided = BriceDeNice.got_his_environment_configuration_provided()
    history = [configuration_provided]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id=BriceDeNice.first_env_configuration_process_id(), events=history
    )

    # Then
    assert process_timeline_view.status == "configuring"
    assert process_timeline_view.type == "dev_environment_setup"


def test_should_be_ready_when_latest_event_is_env_conf_validated():
    # Given
    history = [
        BriceDeNice.got_his_environment_configuration_provided(),
        BriceDeNice.got_his_environment_configuration_validated(),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id=BriceDeNice.first_env_configuration_process_id(), events=history
    )

    # Then
    assert process_timeline_view.status == "ready"
    assert process_timeline_view.type == "dev_environment_setup"


def test_should_be_failed_when_latest_event_is_env_validation_failed():
    # Given
    history = [
        BriceDeNice.got_his_second_environment_configuration_provided(),
        BriceDeNice.got_his_second_environment_configuration_validation_failed(),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id=BriceDeNice.second_env_configuration_process_id(), events=history
    )

    # Then
    assert process_timeline_view.status == "failed"
    assert process_timeline_view.type == "dev_environment_setup"


def test_should_prepared_when_latest_event_is_environment_prepared():
    # Given
    history = [
        BriceDeNice.requested_issue_resolution(),
        BriceDeNice.got_his_environment_prepared(),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id=BriceDeNice.first_env_configuration_process_id(), events=history
    )

    # Then
    assert process_timeline_view.status == "starting"
    assert process_timeline_view.type == "issue_resolution"
