import os
from datetime import datetime
from typing import Any, Literal, Self, Type, assert_never

from cryptography.fernet import Fernet

from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.env_setup.dev_environments_management import (
    ExecutionEnvironmentPreference,
)
from issue_solver.events.domain import (
    AnyDomainEvent,
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
)
from pydantic import BaseModel, Field, AliasChoices

from issue_solver.issues.issue import IssueInfo
from issue_solver.models.supported_models import (
    SupportedAIModel,
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_VERSION,
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
        case type() if event_type is IssueResolutionEnvironmentPrepared:
            return "issue_resolution_environment_prepared"
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
    ai_model: SupportedAIModel = SupportedAnthropicModel.CLAUDE_SONNET_4
    ai_model_version: str | None = LATEST_CLAUDE_4_VERSION
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
    stdout: str
    stderr: str
    return_code: int

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> EnvironmentValidationFailed:
        return EnvironmentValidationFailed(
            occurred_at=self.occurred_at,
            process_id=self.process_id,
            stdout=self.stdout,
            stderr=self.stderr,
            return_code=self.return_code,
        )

    @classmethod
    def create_from(cls, event: EnvironmentValidationFailed) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            process_id=event.process_id,
            stdout=event.stdout,
            stderr=event.stderr,
            return_code=event.return_code,
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
        case _:
            raise Exception(f"Unknown event type: {event_type}")
