import os
from datetime import datetime
from typing import Any, Literal, Self, Type, assert_never

from cryptography.fernet import Fernet

from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.env_setup.dev_environments_management import (
    ExecutionEnvironmentPreference,
)
from issue_solver.env_setup.errors import Phase
from issue_solver.events.domain import (
    AnyDomainEvent,
    Mode,
    CodeRepositoryConnected,
    CodeRepositoryTokenRotated,
    CodeRepositoryIntegrationFailed,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    T,
    IssueResolutionRequested,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    IssueResolutionFailed,
    EnvironmentConfigurationProvided,
    IssueResolutionEnvironmentPrepared,
    EnvironmentConfigurationValidated,
    EnvironmentValidationFailed,
    NotionIntegrationAuthorized,
    NotionIntegrationTokenRefreshed,
    NotionIntegrationAuthorizationFailed,
    DocumentationPromptsDefined,
    DocumentationPromptsRemoved,
    DocumentationGenerationRequested,
    DocumentationGenerationStarted,
    DocumentationGenerationCompleted,
    DocumentationGenerationFailed,
)
from pydantic import BaseModel, Field, AliasChoices

from issue_solver.issues.issue import IssueInfo
from issue_solver.models.supported_models import (
    SupportedAIModel,
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_5_VERSION,
)


def get_record_type(event_type: Type[T]) -> str:
    match event_type:
        case type() if event_type is CodeRepositoryConnected:
            return "repository_connected"
        case type() if event_type is CodeRepositoryTokenRotated:
            return "repository_token_rotated"
        case type() if event_type is CodeRepositoryIntegrationFailed:
            return "repository_integration_failed"
        case type() if event_type is CodeRepositoryIndexed:
            return "repository_indexed"
        case type() if event_type is RepositoryIndexationRequested:
            return "repository_indexation_requested"
        case type() if event_type is IssueResolutionRequested:
            return "issue_resolution_requested"
        case type() if event_type is IssueResolutionStarted:
            return "issue_resolution_started"
        case type() if event_type is IssueResolutionCompleted:
            return "issue_resolution_completed"
        case type() if event_type is IssueResolutionFailed:
            return "issue_resolution_failed"
        case type() if event_type is EnvironmentConfigurationProvided:
            return "environment_configuration_provided"
        case type() if event_type is EnvironmentConfigurationValidated:
            return "environment_configuration_validated"
        case type() if event_type is EnvironmentValidationFailed:
            return "environment_validation_failed"
        case type() if event_type is IssueResolutionEnvironmentPrepared:
            return "issue_resolution_environment_prepared"
        case type() if event_type is NotionIntegrationAuthorized:
            return "notion_integration_authorized"
        case type() if event_type is NotionIntegrationTokenRefreshed:
            return "notion_integration_token_refreshed"
        case type() if event_type is NotionIntegrationAuthorizationFailed:
            return "notion_integration_authorization_failed"
        case type() if event_type is DocumentationPromptsDefined:
            return "documentation_prompts_defined"
        case type() if event_type is DocumentationPromptsRemoved:
            return "documentation_prompts_removed"
        case type() if event_type is DocumentationGenerationRequested:
            return "documentation_generation_requested"
        case type() if event_type is DocumentationGenerationStarted:
            return "documentation_generation_started"
        case type() if event_type is DocumentationGenerationCompleted:
            return "documentation_generation_completed"
        case type() if event_type is DocumentationGenerationFailed:
            return "documentation_generation_failed"
        case _:
            raise Exception(f"Unknown event type: {event_type}")


def _get_encryption_key() -> bytes | None:
    key_str = os.environ.get("TOKEN_ENCRYPTION_KEY")
    if not key_str:
        return None
    return key_str.encode()


def _encrypt_token(plain_token: str) -> str:
    if not plain_token:
        return plain_token

    key = _get_encryption_key()
    if not key:
        return plain_token

    fernet = Fernet(key)
    encrypted_bytes = fernet.encrypt(plain_token.encode())
    return encrypted_bytes.decode()


def _decrypt_token(token: str) -> str:
    if not token:
        return token

    key = _get_encryption_key()
    if not key:
        return token

    try:
        fernet = Fernet(key)
        decrypted_bytes = fernet.decrypt(token.encode())
        return decrypted_bytes.decode()
    except Exception:
        return token


class CodeRepositoryConnectedRecord(BaseModel):
    type: Literal["repository_connected"] = "repository_connected"
    occurred_at: datetime
    url: str
    access_token: str
    user_id: str
    space_id: str
    knowledge_base_id: str
    process_id: str
    token_permissions: dict | None = None

    def safe_copy(self) -> Self:
        return self.model_copy(update={"access_token": obfuscate(self.access_token)})

    def to_domain_event(self) -> CodeRepositoryConnected:
        return CodeRepositoryConnected(
            occurred_at=self.occurred_at,
            url=self.url,
            access_token=_decrypt_token(self.access_token),
            user_id=self.user_id,
            space_id=self.space_id,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            token_permissions=self.token_permissions,
        )

    @classmethod
    def create_from(cls, event: CodeRepositoryConnected) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            url=event.url,
            access_token=_encrypt_token(event.access_token),
            user_id=event.user_id,
            space_id=event.space_id,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            token_permissions=event.token_permissions,
        )


class NotionIntegrationAuthorizedRecord(BaseModel):
    type: Literal["notion_integration_authorized"] = "notion_integration_authorized"
    occurred_at: datetime
    user_id: str
    space_id: str
    process_id: str
    workspace_id: str | None = None
    workspace_name: str | None = None
    bot_id: str | None = None
    mcp_access_token: str | None = None
    mcp_refresh_token: str | None = None
    mcp_token_expires_at: datetime | None = None

    def safe_copy(self) -> Self:
        obfuscated_mcp_access = (
            obfuscate(self.mcp_access_token) if self.mcp_access_token else None
        )
        obfuscated_mcp_refresh = (
            obfuscate(self.mcp_refresh_token) if self.mcp_refresh_token else None
        )
        return self.model_copy(  # type: ignore[call-arg]
            update={
                "mcp_access_token": obfuscated_mcp_access,
                "mcp_refresh_token": obfuscated_mcp_refresh,
            }
        )

    def to_domain_event(self) -> NotionIntegrationAuthorized:
        return NotionIntegrationAuthorized(
            occurred_at=self.occurred_at,
            user_id=self.user_id,
            space_id=self.space_id,
            process_id=self.process_id,
            workspace_id=self.workspace_id,
            workspace_name=self.workspace_name,
            bot_id=self.bot_id,
            mcp_access_token=_decrypt_token(self.mcp_access_token)
            if self.mcp_access_token
            else None,
            mcp_refresh_token=_decrypt_token(self.mcp_refresh_token)
            if self.mcp_refresh_token
            else None,
            mcp_token_expires_at=self.mcp_token_expires_at,
        )

    @classmethod
    def create_from(cls, event: NotionIntegrationAuthorized) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            space_id=event.space_id,
            process_id=event.process_id,
            workspace_id=event.workspace_id,
            workspace_name=event.workspace_name,
            bot_id=event.bot_id,
            mcp_access_token=_encrypt_token(event.mcp_access_token)
            if event.mcp_access_token
            else None,
            mcp_refresh_token=_encrypt_token(event.mcp_refresh_token)
            if event.mcp_refresh_token
            else None,
            mcp_token_expires_at=event.mcp_token_expires_at,
        )


class NotionIntegrationTokenRefreshedRecord(BaseModel):
    type: Literal["notion_integration_token_refreshed"] = (
        "notion_integration_token_refreshed"
    )
    occurred_at: datetime
    user_id: str
    space_id: str
    process_id: str
    workspace_id: str | None = None
    workspace_name: str | None = None
    bot_id: str | None = None
    mcp_access_token: str | None = None
    mcp_refresh_token: str | None = None
    mcp_token_expires_at: datetime | None = None

    def safe_copy(self) -> Self:
        obfuscated_mcp_access = (
            obfuscate(self.mcp_access_token) if self.mcp_access_token else None
        )
        obfuscated_mcp_refresh = (
            obfuscate(self.mcp_refresh_token) if self.mcp_refresh_token else None
        )
        return self.model_copy(  # type: ignore[call-arg]
            update={
                "mcp_access_token": obfuscated_mcp_access,
                "mcp_refresh_token": obfuscated_mcp_refresh,
            }
        )

    def to_domain_event(self) -> NotionIntegrationTokenRefreshed:
        return NotionIntegrationTokenRefreshed(
            occurred_at=self.occurred_at,
            user_id=self.user_id,
            space_id=self.space_id,
            process_id=self.process_id,
            workspace_id=self.workspace_id,
            workspace_name=self.workspace_name,
            bot_id=self.bot_id,
            mcp_access_token=_decrypt_token(self.mcp_access_token)
            if self.mcp_access_token
            else None,
            mcp_refresh_token=_decrypt_token(self.mcp_refresh_token)
            if self.mcp_refresh_token
            else None,
            mcp_token_expires_at=self.mcp_token_expires_at,
        )

    @classmethod
    def create_from(cls, event: NotionIntegrationTokenRefreshed) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            space_id=event.space_id,
            process_id=event.process_id,
            workspace_id=event.workspace_id,
            workspace_name=event.workspace_name,
            bot_id=event.bot_id,
            mcp_access_token=_encrypt_token(event.mcp_access_token)
            if event.mcp_access_token
            else None,
            mcp_refresh_token=_encrypt_token(event.mcp_refresh_token)
            if event.mcp_refresh_token
            else None,
            mcp_token_expires_at=event.mcp_token_expires_at,
        )


class NotionIntegrationAuthorizationFailedRecord(BaseModel):
    type: Literal["notion_integration_authorization_failed"] = (
        "notion_integration_authorization_failed"
    )
    occurred_at: datetime
    error_type: str
    error_message: str
    user_id: str
    space_id: str
    process_id: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> NotionIntegrationAuthorizationFailed:
        return NotionIntegrationAuthorizationFailed(
            occurred_at=self.occurred_at,
            error_type=self.error_type,
            error_message=self.error_message,
            user_id=self.user_id,
            space_id=self.space_id,
            process_id=self.process_id,
        )

    @classmethod
    def create_from(cls, event: NotionIntegrationAuthorizationFailed) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            error_type=event.error_type,
            error_message=event.error_message,
            user_id=event.user_id,
            space_id=event.space_id,
            process_id=event.process_id,
        )


class CodeRepositoryTokenRotatedRecord(BaseModel):
    type: Literal["repository_token_rotated"] = "repository_token_rotated"
    occurred_at: datetime
    knowledge_base_id: str
    new_access_token: str
    user_id: str
    process_id: str
    token_permissions: dict | None = None

    def safe_copy(self) -> Self:
        return self.model_copy(
            update={"new_access_token": obfuscate(self.new_access_token)}
        )

    def to_domain_event(self) -> CodeRepositoryTokenRotated:
        return CodeRepositoryTokenRotated(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            new_access_token=_decrypt_token(self.new_access_token),
            user_id=self.user_id,
            process_id=self.process_id,
            token_permissions=self.token_permissions,
        )

    @classmethod
    def create_from(cls, event: CodeRepositoryTokenRotated) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            new_access_token=_encrypt_token(event.new_access_token),
            user_id=event.user_id,
            process_id=event.process_id,
            token_permissions=event.token_permissions,
        )


class CodeRepositoryIntegrationFailedRecord(BaseModel):
    type: Literal["repository_integration_failed"] = "repository_integration_failed"
    occurred_at: datetime
    url: str
    error_type: str
    error_message: str
    knowledge_base_id: str
    process_id: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> CodeRepositoryIntegrationFailed:
        return CodeRepositoryIntegrationFailed(
            occurred_at=self.occurred_at,
            url=self.url,
            error_type=self.error_type,
            error_message=self.error_message,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
        )

    @classmethod
    def create_from(cls, event: CodeRepositoryIntegrationFailed) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            url=event.url,
            error_type=event.error_type,
            error_message=event.error_message,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
        )


class CodeRepositoryIndexedRecord(BaseModel):
    type: Literal["repository_indexed"] = "repository_indexed"
    occurred_at: datetime
    branch: str
    commit_sha: str
    stats: dict[str, Any]
    knowledge_base_id: str
    process_id: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> CodeRepositoryIndexed:
        return CodeRepositoryIndexed(
            occurred_at=self.occurred_at,
            branch=self.branch,
            commit_sha=self.commit_sha,
            stats=self.stats,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
        )

    @classmethod
    def create_from(cls, event: CodeRepositoryIndexed) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            branch=event.branch,
            commit_sha=event.commit_sha,
            stats=event.stats,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
        )


class RepositoryIndexationRequestedRecord(BaseModel):
    type: Literal["repository_indexation_requested"] = "repository_indexation_requested"
    occurred_at: datetime
    knowledge_base_id: str
    process_id: str
    user_id: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> RepositoryIndexationRequested:
        return RepositoryIndexationRequested(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            user_id=self.user_id,
        )

    @classmethod
    def create_from(cls, event: RepositoryIndexationRequested) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            user_id=event.user_id,
        )


class IssueResolutionRequestedRecord(BaseModel):
    type: Literal["issue_resolution_requested"] = "issue_resolution_requested"
    occurred_at: datetime
    knowledge_base_id: str
    process_id: str
    issue: IssueInfo
    user_id: str | None = None
    agent: SupportedAgent = SupportedAgent.CLAUDE_CODE
    max_turns: int = 100
    ai_model: SupportedAIModel = SupportedAnthropicModel.CLAUDE_SONNET_4_5
    ai_model_version: str | None = LATEST_CLAUDE_4_5_VERSION
    execution_environment: ExecutionEnvironmentPreference = (
        ExecutionEnvironmentPreference.NO_ENV_REQUIRED
    )

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> IssueResolutionRequested:
        return IssueResolutionRequested(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            issue=self.issue,
            user_id=self.user_id if self.user_id is not None else "unknown",
            agent=self.agent,
            max_turns=self.max_turns,
            ai_model=self.ai_model,
            ai_model_version=self.ai_model_version,
            execution_environment=self.execution_environment,
        )

    @classmethod
    def create_from(cls, event: IssueResolutionRequested) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            issue=event.issue,
            user_id=event.user_id,
            agent=event.agent,
            max_turns=event.max_turns,
            ai_model=event.ai_model,
            ai_model_version=event.ai_model_version,
            execution_environment=event.execution_environment,
        )


class IssueResolutionStartedRecord(BaseModel):
    type: Literal["issue_resolution_started"] = "issue_resolution_started"
    occurred_at: datetime
    process_id: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> IssueResolutionStarted:
        return IssueResolutionStarted(
            occurred_at=self.occurred_at,
            process_id=self.process_id,
        )

    @classmethod
    def create_from(cls, event: IssueResolutionStarted) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            process_id=event.process_id,
        )


class IssueResolutionCompletedRecord(BaseModel):
    type: Literal["issue_resolution_completed"] = "issue_resolution_completed"
    occurred_at: datetime
    process_id: str
    pr_number: int
    pr_url: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> IssueResolutionCompleted:
        return IssueResolutionCompleted(
            occurred_at=self.occurred_at,
            process_id=self.process_id,
            pr_number=self.pr_number,
            pr_url=self.pr_url,
        )

    @classmethod
    def create_from(cls, event: IssueResolutionCompleted) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            process_id=event.process_id,
            pr_number=event.pr_number,
            pr_url=event.pr_url,
        )


class IssueResolutionFailedRecord(BaseModel):
    type: Literal["issue_resolution_failed"] = "issue_resolution_failed"
    occurred_at: datetime
    process_id: str
    reason: str
    error_message: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> IssueResolutionFailed:
        return IssueResolutionFailed(
            occurred_at=self.occurred_at,
            process_id=self.process_id,
            reason=self.reason,
            error_message=self.error_message,
        )

    @classmethod
    def create_from(cls, event: IssueResolutionFailed) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            process_id=event.process_id,
            reason=event.reason,
            error_message=event.error_message,
        )


class EnvironmentConfigurationProvidedRecord(BaseModel):
    type: Literal["environment_configuration_provided"] = (
        "environment_configuration_provided"
    )
    environment_id: str
    occurred_at: datetime
    knowledge_base_id: str
    user_id: str
    process_id: str
    project_setup: str = Field(
        validation_alias=AliasChoices(
            "project_setup",
            "script",
        )
    )
    global_setup: str | None = None

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> EnvironmentConfigurationProvided:
        return EnvironmentConfigurationProvided(
            environment_id=self.environment_id,
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            user_id=self.user_id,
            process_id=self.process_id,
            project_setup=self.project_setup,
            global_setup=self.global_setup,
        )

    @classmethod
    def create_from(cls, event: EnvironmentConfigurationProvided) -> Self:
        return cls(
            environment_id=event.environment_id,
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            user_id=event.user_id,
            process_id=event.process_id,
            project_setup=event.project_setup,
            global_setup=event.global_setup,
        )


class IssueResolutionEnvironmentPreparedRecord(BaseModel):
    type: Literal["issue_resolution_environment_prepared"] = (
        "issue_resolution_environment_prepared"
    )
    environment_id: str
    instance_id: str
    occurred_at: datetime
    knowledge_base_id: str
    process_id: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> IssueResolutionEnvironmentPrepared:
        return IssueResolutionEnvironmentPrepared(
            environment_id=self.environment_id,
            instance_id=self.instance_id,
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
        )

    @classmethod
    def create_from(cls, event: IssueResolutionEnvironmentPrepared) -> Self:
        return cls(
            environment_id=event.environment_id,
            instance_id=event.instance_id,
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
        )


class EnvironmentConfigurationValidatedRecord(BaseModel):
    type: Literal["environment_configuration_validated"] = (
        "environment_configuration_validated"
    )
    snapshot_id: str
    occurred_at: datetime
    process_id: str
    stdout: str
    stderr: str
    return_code: int

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> EnvironmentConfigurationValidated:
        return EnvironmentConfigurationValidated(
            snapshot_id=self.snapshot_id,
            occurred_at=self.occurred_at,
            process_id=self.process_id,
            stdout=self.stdout,
            stderr=self.stderr,
            return_code=self.return_code,
        )

    @classmethod
    def create_from(cls, event: EnvironmentConfigurationValidated) -> Self:
        return cls(
            snapshot_id=event.snapshot_id,
            occurred_at=event.occurred_at,
            process_id=event.process_id,
            stdout=event.stdout,
            stderr=event.stderr,
            return_code=event.return_code,
        )


class EnvironmentValidationFailedRecord(BaseModel):
    type: Literal["environment_validation_failed"] = "environment_validation_failed"
    occurred_at: datetime
    process_id: str
    phase: Phase | None = None
    stdout: str
    stderr: str
    return_code: int

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> EnvironmentValidationFailed:
        return EnvironmentValidationFailed(
            occurred_at=self.occurred_at,
            process_id=self.process_id,
            phase=self.phase if self.phase is not None else Phase.PROJECT_SETUP,
            stdout=self.stdout,
            stderr=self.stderr,
            return_code=self.return_code,
        )

    @classmethod
    def create_from(cls, event: EnvironmentValidationFailed) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            process_id=event.process_id,
            phase=event.phase,
            stdout=event.stdout,
            stderr=event.stderr,
            return_code=event.return_code,
        )


class DocumentationPromptsDefinedRecord(BaseModel):
    type: Literal["documentation_prompts_defined"] = "documentation_prompts_defined"
    knowledge_base_id: str
    user_id: str
    docs_prompts: dict[str, str]
    process_id: str
    occurred_at: datetime

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> DocumentationPromptsDefined:
        return DocumentationPromptsDefined(
            knowledge_base_id=self.knowledge_base_id,
            user_id=self.user_id,
            docs_prompts=self.docs_prompts,
            process_id=self.process_id,
            occurred_at=self.occurred_at,
        )

    @classmethod
    def create_from(cls, event: DocumentationPromptsDefined) -> Self:
        return cls(
            knowledge_base_id=event.knowledge_base_id,
            user_id=event.user_id,
            docs_prompts=event.docs_prompts,
            process_id=event.process_id,
            occurred_at=event.occurred_at,
        )


class DocumentationPromptsRemovedRecord(BaseModel):
    type: Literal["documentation_prompts_removed"] = "documentation_prompts_removed"
    knowledge_base_id: str
    user_id: str
    prompt_ids: set[str]
    process_id: str
    occurred_at: datetime

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> DocumentationPromptsRemoved:
        return DocumentationPromptsRemoved(
            knowledge_base_id=self.knowledge_base_id,
            user_id=self.user_id,
            prompt_ids=self.prompt_ids,
            process_id=self.process_id,
            occurred_at=self.occurred_at,
        )

    @classmethod
    def create_from(cls, event: DocumentationPromptsRemoved) -> Self:
        return cls(
            knowledge_base_id=event.knowledge_base_id,
            user_id=event.user_id,
            prompt_ids=event.prompt_ids,
            process_id=event.process_id,
            occurred_at=event.occurred_at,
        )


class DocumentationGenerationRequestedRecord(BaseModel):
    type: Literal["documentation_generation_requested"] = (
        "documentation_generation_requested"
    )
    knowledge_base_id: str
    prompt_id: str
    prompt_description: str
    code_version: str
    run_id: str
    process_id: str
    occurred_at: datetime
    mode: Mode = Field(default="complete")

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> DocumentationGenerationRequested:
        return DocumentationGenerationRequested(
            knowledge_base_id=self.knowledge_base_id,
            prompt_id=self.prompt_id,
            prompt_description=self.prompt_description,
            code_version=self.code_version,
            run_id=self.run_id,
            process_id=self.process_id,
            occurred_at=self.occurred_at,
            mode=self.mode or "complete",
        )

    @classmethod
    def create_from(cls, event: DocumentationGenerationRequested) -> Self:
        return cls(
            knowledge_base_id=event.knowledge_base_id,
            prompt_id=event.prompt_id,
            prompt_description=event.prompt_description,
            code_version=event.code_version,
            run_id=event.run_id,
            process_id=event.process_id,
            occurred_at=event.occurred_at,
            mode=event.mode,
        )


class DocumentationGenerationStartedRecord(BaseModel):
    type: Literal["documentation_generation_started"] = (
        "documentation_generation_started"
    )
    knowledge_base_id: str
    prompt_id: str
    code_version: str
    run_id: str
    process_id: str
    occurred_at: datetime

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> DocumentationGenerationStarted:
        return DocumentationGenerationStarted(
            knowledge_base_id=self.knowledge_base_id,
            prompt_id=self.prompt_id,
            code_version=self.code_version,
            run_id=self.run_id,
            process_id=self.process_id,
            occurred_at=self.occurred_at,
        )

    @classmethod
    def create_from(cls, event: DocumentationGenerationStarted) -> Self:
        return cls(
            knowledge_base_id=event.knowledge_base_id,
            prompt_id=event.prompt_id,
            code_version=event.code_version,
            run_id=event.run_id,
            process_id=event.process_id,
            occurred_at=event.occurred_at,
        )


class DocumentationGenerationCompletedRecord(BaseModel):
    type: Literal["documentation_generation_completed"] = (
        "documentation_generation_completed"
    )
    knowledge_base_id: str
    prompt_id: str
    code_version: str
    run_id: str
    generated_documents: list[str]
    process_id: str
    occurred_at: datetime

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> DocumentationGenerationCompleted:
        return DocumentationGenerationCompleted(
            knowledge_base_id=self.knowledge_base_id,
            prompt_id=self.prompt_id,
            code_version=self.code_version,
            run_id=self.run_id,
            generated_documents=self.generated_documents,
            process_id=self.process_id,
            occurred_at=self.occurred_at,
        )

    @classmethod
    def create_from(cls, event: DocumentationGenerationCompleted) -> Self:
        return cls(
            knowledge_base_id=event.knowledge_base_id,
            prompt_id=event.prompt_id,
            code_version=event.code_version,
            run_id=event.run_id,
            generated_documents=event.generated_documents,
            process_id=event.process_id,
            occurred_at=event.occurred_at,
        )


class DocumentationGenerationFailedRecord(BaseModel):
    type: Literal["documentation_generation_failed"] = "documentation_generation_failed"
    knowledge_base_id: str
    prompt_id: str
    code_version: str
    run_id: str
    error_message: str
    process_id: str
    occurred_at: datetime

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> DocumentationGenerationFailed:
        return DocumentationGenerationFailed(
            knowledge_base_id=self.knowledge_base_id,
            prompt_id=self.prompt_id,
            code_version=self.code_version,
            run_id=self.run_id,
            error_message=self.error_message,
            process_id=self.process_id,
            occurred_at=self.occurred_at,
        )

    @classmethod
    def create_from(cls, event: DocumentationGenerationFailed) -> Self:
        return cls(
            knowledge_base_id=event.knowledge_base_id,
            prompt_id=event.prompt_id,
            code_version=event.code_version,
            run_id=event.run_id,
            error_message=event.error_message,
            process_id=event.process_id,
            occurred_at=event.occurred_at,
        )


ProcessTimelineEventRecords = (
    CodeRepositoryConnectedRecord
    | CodeRepositoryTokenRotatedRecord
    | CodeRepositoryIntegrationFailedRecord
    | CodeRepositoryIndexedRecord
    | RepositoryIndexationRequestedRecord
    | IssueResolutionRequestedRecord
    | IssueResolutionStartedRecord
    | IssueResolutionCompletedRecord
    | IssueResolutionFailedRecord
    | EnvironmentConfigurationProvidedRecord
    | IssueResolutionEnvironmentPreparedRecord
    | EnvironmentConfigurationValidatedRecord
    | EnvironmentValidationFailedRecord
    | NotionIntegrationAuthorizedRecord
    | NotionIntegrationTokenRefreshedRecord
    | NotionIntegrationAuthorizationFailedRecord
    | DocumentationPromptsDefinedRecord
    | DocumentationPromptsRemovedRecord
    | DocumentationGenerationRequestedRecord
    | DocumentationGenerationStartedRecord
    | DocumentationGenerationCompletedRecord
    | DocumentationGenerationFailedRecord
)


def obfuscate(secret: str) -> str:
    return "*" * (len(secret) - 4) + secret[-4:]


def serialize(event: AnyDomainEvent) -> ProcessTimelineEventRecords:
    match event:
        case CodeRepositoryConnected():
            return CodeRepositoryConnectedRecord.create_from(event)
        case CodeRepositoryTokenRotated():
            return CodeRepositoryTokenRotatedRecord.create_from(event)
        case CodeRepositoryIntegrationFailed():
            return CodeRepositoryIntegrationFailedRecord.create_from(event)
        case CodeRepositoryIndexed():
            return CodeRepositoryIndexedRecord.create_from(event)
        case RepositoryIndexationRequested():
            return RepositoryIndexationRequestedRecord.create_from(event)
        case IssueResolutionRequested():
            return IssueResolutionRequestedRecord.create_from(event)
        case IssueResolutionStarted():
            return IssueResolutionStartedRecord.create_from(event)
        case IssueResolutionCompleted():
            return IssueResolutionCompletedRecord.create_from(event)
        case IssueResolutionFailed():
            return IssueResolutionFailedRecord.create_from(event)
        case EnvironmentConfigurationProvided():
            return EnvironmentConfigurationProvidedRecord.create_from(event)
        case IssueResolutionEnvironmentPrepared():
            return IssueResolutionEnvironmentPreparedRecord.create_from(event)
        case EnvironmentConfigurationValidated():
            return EnvironmentConfigurationValidatedRecord.create_from(event)
        case EnvironmentValidationFailed():
            return EnvironmentValidationFailedRecord.create_from(event)
        case NotionIntegrationAuthorized():
            return NotionIntegrationAuthorizedRecord.create_from(event)
        case NotionIntegrationTokenRefreshed():
            return NotionIntegrationTokenRefreshedRecord.create_from(event)
        case NotionIntegrationAuthorizationFailed():
            return NotionIntegrationAuthorizationFailedRecord.create_from(event)
        case DocumentationPromptsDefined():
            return DocumentationPromptsDefinedRecord.create_from(event)
        case DocumentationPromptsRemoved():
            return DocumentationPromptsRemovedRecord.create_from(event)
        case DocumentationGenerationRequested():
            return DocumentationGenerationRequestedRecord.create_from(event)
        case DocumentationGenerationStarted():
            return DocumentationGenerationStartedRecord.create_from(event)
        case DocumentationGenerationCompleted():
            return DocumentationGenerationCompletedRecord.create_from(event)
        case DocumentationGenerationFailed():
            return DocumentationGenerationFailedRecord.create_from(event)
        case _:
            assert_never(event)


def deserialize(event_type: str, data: str) -> AnyDomainEvent:
    match event_type:
        case "repository_connected":
            return CodeRepositoryConnectedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "repository_token_rotated":
            return CodeRepositoryTokenRotatedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "repository_integration_failed":
            return CodeRepositoryIntegrationFailedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "repository_indexed":
            return CodeRepositoryIndexedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "repository_indexation_requested":
            return RepositoryIndexationRequestedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "issue_resolution_requested":
            return IssueResolutionRequestedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "issue_resolution_started":
            return IssueResolutionStartedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "issue_resolution_completed":
            return IssueResolutionCompletedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "issue_resolution_failed":
            return IssueResolutionFailedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "environment_configuration_provided":
            return EnvironmentConfigurationProvidedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "issue_resolution_environment_prepared":
            return IssueResolutionEnvironmentPreparedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "environment_configuration_validated":
            return EnvironmentConfigurationValidatedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "environment_validation_failed":
            return EnvironmentValidationFailedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "notion_integration_authorized":
            return NotionIntegrationAuthorizedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "notion_integration_token_refreshed":
            return NotionIntegrationTokenRefreshedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "notion_integration_authorization_failed":
            return NotionIntegrationAuthorizationFailedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "documentation_prompts_defined":
            return DocumentationPromptsDefinedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "documentation_prompts_removed":
            return DocumentationPromptsRemovedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "documentation_generation_requested":
            return DocumentationGenerationRequestedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "documentation_generation_started":
            return DocumentationGenerationStartedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "documentation_generation_completed":
            return DocumentationGenerationCompletedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "documentation_generation_failed":
            return DocumentationGenerationFailedRecord.model_validate_json(
                data
            ).to_domain_event()
        case _:
            raise Exception(f"Unknown event type: {event_type}")
