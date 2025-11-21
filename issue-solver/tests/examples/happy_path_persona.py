from datetime import datetime

from issue_solver.env_setup.errors import Phase
from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryTokenRotated,
    CodeRepositoryIntegrationFailed,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    IssueResolutionRequested,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    IssueResolutionFailed,
    EnvironmentConfigurationProvided,
    IssueResolutionEnvironmentPrepared,
    AnyDomainEvent,
    EnvironmentConfigurationValidated,
    EnvironmentValidationFailed,
    NotionIntegrationAuthorized,
    NotionIntegrationTokenRefreshed,
    DocumentationPromptsDefined,
    DocumentationGenerationRequested,
    DocumentationGenerationStarted,
    DocumentationGenerationCompleted,
    DocumentationGenerationFailed,
)
from issue_solver.issues.issue import IssueInfo


class BriceDeNice:
    @classmethod
    def first_repo_integration_process_id(cls):
        return "brice-code-integration-process-001"

    @classmethod
    def got_his_first_repo_connected(cls) -> CodeRepositoryConnected:
        return CodeRepositoryConnected(
            process_id=cls.first_repo_integration_process_id(),
            url="https://github.com/brice/nice-repo.git",
            access_token="ghp_brices_token_123456",
            user_id=cls.user_id(),
            space_id=cls.team_space_id(),
            knowledge_base_id="brice-kb-001",
            occurred_at=datetime.fromisoformat("2025-01-01T12:00:00Z"),
            token_permissions={
                "scopes": ["repo", "workflow", "read:user"],
                "has_repo": True,
                "has_workflow": True,
                "has_read_user": True,
                "missing_scopes": [],
                "is_optimal": True,
            },
        )

    @classmethod
    def team_space_id(cls) -> str:
        return "brice-space-001"

    @classmethod
    def connected_notion_workspace(cls) -> NotionIntegrationAuthorized:
        return NotionIntegrationAuthorized(
            process_id=cls.notion_integration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-01T12:05:00Z"),
            user_id=cls.user_id(),
            space_id=cls.team_space_id(),
            workspace_id="brice-notion-workspace",
            workspace_name="Brice Knowledge Base",
            bot_id="notion-bot-001",
            mcp_access_token="notion_brice_token_987654",
            mcp_refresh_token="notion_brice_refresh_token_123",
        )

    @classmethod
    def user_id(cls) -> str:
        return "brice-user-001"

    @classmethod
    def notion_integration_process_id(cls) -> str:
        return "brice-notion-integration-process-001"

    @classmethod
    def rotated_notion_token(cls) -> NotionIntegrationTokenRefreshed:
        return NotionIntegrationTokenRefreshed(
            process_id=BriceDeNice.notion_integration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-03T08:30:00Z"),
            user_id=BriceDeNice.user_id(),
            space_id=BriceDeNice.team_space_id(),
            workspace_id="brice-notion-workspace",
            workspace_name="Brice Knowledge Base",
            bot_id="notion-bot-001",
            mcp_access_token="notion_brice_new_token_4321",
            mcp_refresh_token="notion_brice_new_refresh_token_4321",
        )

    @classmethod
    def got_his_first_repo_indexed(cls) -> CodeRepositoryIndexed:
        return CodeRepositoryIndexed(
            process_id=cls.first_repo_integration_process_id(),
            branch="main",
            commit_sha="def456ghijkl",
            stats={"files_indexed": 42, "lines_indexed": 2048},
            knowledge_base_id="brice-kb-001",
            occurred_at=datetime.fromisoformat("2025-01-01T12:00:30Z"),
        )

    @classmethod
    def first_issue_resolution_process_id(cls):
        return "brice-process-002"

    @classmethod
    def got_his_environment_configuration_provided(
        cls,
    ) -> EnvironmentConfigurationProvided:
        return EnvironmentConfigurationProvided(
            process_id=BriceDeNice.first_env_configuration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-02T08:00:00Z"),
            user_id=cls.user_id(),
            knowledge_base_id="brice-kb-001",
            global_setup="""
            #!/bin/bash
            apt-get update && apt-get install -y pip3 python3-pip
            curl -LsSf https://astral.sh/uv/install.sh | sh
            """,
            project_setup="""
            #!/bin/bash
            # install dependencies
            apt-get update && apt-get install -y libssl-dev libffi-dev python3-dev
            pip install -r requirements.txt
            """,
            environment_id="brice-environment-001",
        )

    @classmethod
    def first_env_configuration_process_id(cls) -> str:
        return "brice-environment-configuration-process-001"

    @classmethod
    def got_his_environment_configuration_validated(
        cls,
    ) -> EnvironmentConfigurationValidated:
        return EnvironmentConfigurationValidated(
            process_id=BriceDeNice.first_env_configuration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-02T08:01:05Z"),
            snapshot_id="brice-env-001-snap-001",
            stdout="environment setup completed successfully",
            stderr="no errors",
            return_code=0,
        )

    @classmethod
    def got_his_second_environment_configuration_provided(
        cls,
    ) -> EnvironmentConfigurationProvided:
        return EnvironmentConfigurationProvided(
            process_id=BriceDeNice.second_env_configuration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-02T08:02:00Z"),
            user_id=BriceDeNice.user_id(),
            knowledge_base_id="brice-kb-001",
            global_setup="""
            #!/bin/bash
            missing_command
            """,
            project_setup="""
            #!/bin/bash
            bad_command
            """,
            environment_id="brice-environment-001",
        )

    @classmethod
    def second_env_configuration_process_id(cls) -> str:
        return "brice-environment-configuration-process-002"

    @classmethod
    def got_his_second_environment_configuration_validation_failed(
        cls,
    ) -> EnvironmentValidationFailed:
        return EnvironmentValidationFailed(
            phase=Phase.GLOBAL_SETUP,
            process_id=BriceDeNice.second_env_configuration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-02T08:02:15Z"),
            stdout="",
            stderr="bash: missing_command: command not found",
            return_code=127,
        )

    @classmethod
    def requested_repository_indexation(cls) -> RepositoryIndexationRequested:
        return RepositoryIndexationRequested(
            process_id="brice-indexation-process-001",
            occurred_at=datetime.fromisoformat("2025-01-01T12:00:15Z"),
            user_id=BriceDeNice.user_id(),
            knowledge_base_id="brice-kb-001",
        )

    @classmethod
    def requested_issue_resolution(cls) -> IssueResolutionRequested:
        return IssueResolutionRequested(
            process_id=cls.first_issue_resolution_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-02T09:00:00Z"),
            user_id=BriceDeNice.user_id(),
            knowledge_base_id="brice-kb-001",
            issue=IssueInfo(
                title="Fix login bug",
                description="Users are unable to log in with correct credentials.",
            ),
        )

    @classmethod
    def got_his_environment_prepared(cls) -> IssueResolutionEnvironmentPrepared:
        return IssueResolutionEnvironmentPrepared(
            process_id="brice-environment-preparation-process-001",
            occurred_at=datetime.fromisoformat("2025-01-02T09:00:10Z"),
            environment_id="brice-environment-001",
            instance_id="i-brice-env-instance-001",
            knowledge_base_id="brice-kb-001",
        )

    @classmethod
    def started_issue_resolution(cls) -> IssueResolutionStarted:
        return IssueResolutionStarted(
            process_id=cls.first_issue_resolution_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-02T09:05:00Z"),
        )

    @classmethod
    def completed_issue_resolution(cls) -> IssueResolutionCompleted:
        return IssueResolutionCompleted(
            process_id=cls.first_issue_resolution_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-02T10:30:00Z"),
            pr_url="https://github.com/brice/nice-repo/pull/42",
            pr_number=42,
        )

    @classmethod
    def got_his_token_rotated(cls) -> CodeRepositoryTokenRotated:
        return CodeRepositoryTokenRotated(
            process_id="brice-token-rotation-process-001",
            occurred_at=datetime.fromisoformat("2025-01-03T08:00:00Z"),
            user_id=BriceDeNice.user_id(),
            knowledge_base_id="brice-kb-001",
            new_access_token="ghp_brices_new_token_789012",
            token_permissions={
                "scopes": ["repo", "workflow", "read:user"],
                "has_repo": True,
                "has_workflow": True,
                "has_read_user": True,
                "missing_scopes": [],
                "is_optimal": True,
            },
        )

    @classmethod
    def second_issue_resolution_process_id(cls):
        return "brice-process-003"

    @classmethod
    def requested_second_issue_resolution(cls) -> IssueResolutionRequested:
        return IssueResolutionRequested(
            process_id=cls.second_issue_resolution_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-03T14:00:00Z"),
            user_id=BriceDeNice.user_id(),
            knowledge_base_id="brice-kb-001",
            issue=IssueInfo(
                title="Performance issue in data processing",
                description="The data processing pipeline is too slow when handling large datasets over 1GB.",
            ),
        )

    @classmethod
    def failed_second_issue_resolution(cls) -> IssueResolutionFailed:
        return IssueResolutionFailed(
            process_id=cls.second_issue_resolution_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-03T16:45:00Z"),
            reason="complexity_exceeded",
            error_message="The issue requires architectural changes that exceed the agent's current capabilities. Manual intervention recommended for performance optimization of the data pipeline.",
        )

    @classmethod
    def failed_second_repo_integration(cls) -> CodeRepositoryIntegrationFailed:
        return CodeRepositoryIntegrationFailed(
            process_id="brice-second-repo-integration-process-001",
            occurred_at=datetime.fromisoformat("2025-01-04T11:30:00Z"),
            url="https://github.com/brice/private-enterprise-repo.git",
            knowledge_base_id="brice-kb-001",
            error_type="access_denied",
            error_message="Repository access denied. Token does not have sufficient permissions for private enterprise repository.",
        )

    @classmethod
    def defined_prompts_for_documentation(cls) -> dict[str, str]:
        return {
            "domain_events_glossary": (
                "Generate a comprehensive glossary of all domain events used in the codebase, "
                "including their purpose and usage examples."
            ),
            "adrs": (
                "Create Architecture Decision Records (ADRs) for significant architectural choices made in the project, "
                "detailing the context, decision, and consequences of each choice."
            ),
        }

    @classmethod
    def doc_configuration_process_id(cls) -> str:
        return "brice-doc-configuration-process-001"

    @classmethod
    def has_defined_documentation_prompts(cls) -> DocumentationPromptsDefined:
        return DocumentationPromptsDefined(
            process_id=cls.doc_configuration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-01T12:10:00Z"),
            user_id=cls.user_id(),
            knowledge_base_id="brice-kb-001",
            docs_prompts=cls.defined_prompts_for_documentation(),
        )

    @classmethod
    def defined_additional_prompts_for_documentation(cls) -> dict[str, str]:
        return {
            "api_documentation": (
                "Generate detailed API documentation for all endpoints, including request/response examples and error codes."
            ),
            "setup_guide": (
                "Create a comprehensive setup guide for new developers, covering environment setup, dependencies, and common workflows."
            ),
        }

    @classmethod
    def has_defined_additional_documentation_prompts(
        cls,
    ) -> DocumentationPromptsDefined:
        return DocumentationPromptsDefined(
            process_id=cls.doc_configuration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-04T12:15:00Z"),
            user_id=cls.user_id(),
            knowledge_base_id="brice-kb-001",
            docs_prompts=cls.defined_additional_prompts_for_documentation(),
        )

    @classmethod
    def has_changed_documentation_prompts(cls) -> DocumentationPromptsDefined:
        return DocumentationPromptsDefined(
            process_id=cls.doc_configuration_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-05T09:20:00Z"),
            user_id=cls.user_id(),
            knowledge_base_id="brice-kb-001",
            docs_prompts={
                "domain_events_glossary": (
                    "Update the glossary of domain events to include recent additions and provide clearer usage examples."
                ),
                "adrs": (
                    "Revise existing Architecture Decision Records (ADRs) to reflect changes in architectural choices and their implications."
                ),
            },
        )

    @classmethod
    def doc_generation_process_id(cls) -> str:
        return "brice-doc-generation-process-001"

    @classmethod
    def requested_documentation_generation(cls) -> DocumentationGenerationRequested:
        return DocumentationGenerationRequested(
            knowledge_base_id="brice-kb-001",
            prompt_id="domain_events_glossary",
            prompt_description=(
                "Update the glossary of domain events to include recent additions and provide clearer usage examples."
            ),
            code_version=cls.got_his_first_repo_indexed().commit_sha,
            run_id=cls.has_changed_documentation_prompts().process_id,
            process_id=cls.doc_generation_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-06T08:05:00Z"),
            mode="update",
        )

    @classmethod
    def started_documentation_generation(cls) -> DocumentationGenerationStarted:
        return DocumentationGenerationStarted(
            knowledge_base_id="brice-kb-001",
            prompt_id="domain_events_glossary",
            code_version=cls.got_his_first_repo_indexed().commit_sha,
            run_id=cls.has_changed_documentation_prompts().process_id,
            process_id=cls.doc_generation_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-06T08:05:30Z"),
        )

    @classmethod
    def generated_documentation_completed(cls) -> DocumentationGenerationCompleted:
        return DocumentationGenerationCompleted(
            knowledge_base_id="brice-kb-001",
            prompt_id="domain_events_glossary",
            code_version=cls.got_his_first_repo_indexed().commit_sha,
            run_id=cls.has_changed_documentation_prompts().process_id,
            generated_documents=["domain_events_glossary.md"],
            process_id=cls.doc_generation_process_id(),
            occurred_at=datetime.fromisoformat("2025-01-06T08:07:00Z"),
        )

    @classmethod
    def generated_documentation_failed(cls) -> DocumentationGenerationFailed:
        return DocumentationGenerationFailed(
            knowledge_base_id="brice-kb-001",
            prompt_id="overview",
            code_version=cls.got_his_first_repo_indexed().commit_sha,
            run_id=cls.has_changed_documentation_prompts().process_id,
            error_message="Claude Code agent failed: missing context",
            process_id="brice-doc-generation-process-002",
            occurred_at=datetime.fromisoformat("2025-01-06T09:15:00Z"),
        )

    @classmethod
    def all_events(cls) -> list[AnyDomainEvent]:
        """
        Returns all domain events in chronological order, representing a complete
        user journey from repository integration through issue resolution.
        """
        return [
            # Day 1: Repository integration and setup
            cls.got_his_first_repo_connected(),  # 12:00:00 - Repo connected
            cls.requested_repository_indexation(),  # 12:00:15 - Indexation requested
            cls.got_his_first_repo_indexed(),  # 12:00:30 - Repo indexed
            cls.connected_notion_workspace(),  # 11:00:00 - Notion workspace connected
            # Day 2: Environment setup and first issue resolution
            cls.got_his_environment_configuration_provided(),  # 08:00:00 - Environment config provided
            cls.got_his_environment_configuration_validated(),  # 08:01:05 - Environment config validated
            cls.got_his_second_environment_configuration_provided(),
            cls.got_his_second_environment_configuration_validation_failed(),
            cls.requested_issue_resolution(),  # 09:00:00 - First issue requested
            cls.got_his_environment_prepared(),  # 09:00:10 - Environment prepared
            cls.started_issue_resolution(),  # 09:05:00 - Issue resolution started
            cls.completed_issue_resolution(),  # 10:30:00 - Issue resolved with PR
            # Day 3: Token rotation and second issue (failed)
            cls.got_his_token_rotated(),  # 08:00:00 - Token rotated for security
            cls.rotated_notion_token(),  # 07:30:00 - Notion token rotated
            cls.requested_second_issue_resolution(),  # 14:00:00 - Second issue requested
            cls.failed_second_issue_resolution(),  # 16:45:00 - Second issue failed
            # Day 4: Failed integration attempt
            cls.failed_second_repo_integration(),  # 11:30:00 - Failed repo integration
            cls.has_defined_documentation_prompts(),
            cls.has_defined_additional_documentation_prompts(),
            cls.has_changed_documentation_prompts(),
            cls.requested_documentation_generation(),
            cls.started_documentation_generation(),
            cls.generated_documentation_completed(),
            cls.generated_documentation_failed(),
        ]


def examples_of_all_events() -> list[tuple[type[AnyDomainEvent], AnyDomainEvent]]:
    return [(type(event), event) for event in BriceDeNice.all_events()]
