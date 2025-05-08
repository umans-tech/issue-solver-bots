from datetime import datetime
from typing import Any, Literal, Self, Type, assert_never

from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryIntegrationFailed,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    CodingAgentRequested,
    CodingAgentImplementationStarted,
    CodingAgentImplementationCompleted,
    CodingAgentImplementationFailed,
    PullRequestCreated,
    T,
)
from pydantic import BaseModel


def get_record_type(event_type: Type[T]) -> str:
    match event_type:
        case type() if event_type is CodeRepositoryConnected:
            return "repository_connected"
        case type() if event_type is CodeRepositoryIntegrationFailed:
            return "repository_integration_failed"
        case type() if event_type is CodeRepositoryIndexed:
            return "repository_indexed"
        case type() if event_type is RepositoryIndexationRequested:
            return "repository_indexation_requested"
        case type() if event_type is CodingAgentRequested:
            return "coding_agent_requested"
        case type() if event_type is CodingAgentImplementationStarted:
            return "coding_agent_implementation_started"
        case type() if event_type is CodingAgentImplementationCompleted:
            return "coding_agent_implementation_completed"
        case type() if event_type is CodingAgentImplementationFailed:
            return "coding_agent_implementation_failed"
        case type() if event_type is PullRequestCreated:
            return "pull_request_created"
        case _:
            raise Exception(f"Unknown event type: {event_type}")


class CodeRepositoryConnectedRecord(BaseModel):
    type: Literal["repository_connected"] = "repository_connected"
    occurred_at: datetime
    url: str
    access_token: str
    user_id: str
    space_id: str
    knowledge_base_id: str
    process_id: str

    def safe_copy(self) -> Self:
        return self.model_copy(update={"access_token": obfuscate(self.access_token)})

    def to_domain_event(self) -> CodeRepositoryConnected:
        return CodeRepositoryConnected(
            occurred_at=self.occurred_at,
            url=self.url,
            access_token=self.access_token,
            user_id=self.user_id,
            space_id=self.space_id,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
        )

    @classmethod
    def create_from(cls, event: CodeRepositoryConnected) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            url=event.url,
            access_token=event.access_token,
            user_id=event.user_id,
            space_id=event.space_id,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
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


class PullRequestCreatedRecord(BaseModel):
    type: Literal["pull_request_created"] = "pull_request_created"
    occurred_at: datetime
    knowledge_base_id: str
    process_id: str
    user_id: str
    pr_title: str
    pr_description: str
    pr_url: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> PullRequestCreated:
        return PullRequestCreated(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            user_id=self.user_id,
            pr_title=self.pr_title,
            pr_description=self.pr_description,
            pr_url=self.pr_url,
        )

    @classmethod
    def create_from(cls, event: PullRequestCreated) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            user_id=event.user_id,
            pr_title=event.pr_title,
            pr_description=event.pr_description,
            pr_url=event.pr_url,
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


class CodingAgentRequestedRecord(BaseModel):
    type: Literal["coding_agent_requested"] = "coding_agent_requested"
    occurred_at: datetime
    knowledge_base_id: str
    process_id: str
    user_id: str
    task_description: str
    branch_name: str
    pr_title: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> CodingAgentRequested:
        return CodingAgentRequested(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            user_id=self.user_id,
            task_description=self.task_description,
            branch_name=self.branch_name,
            pr_title=self.pr_title,
        )

    @classmethod
    def create_from(cls, event: CodingAgentRequested) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            user_id=event.user_id,
        )


class CodingAgentImplementationStartedRecord(BaseModel):
    type: Literal["coding_agent_implementation_started"] = "coding_agent_implementation_started"
    occurred_at: datetime
    knowledge_base_id: str
    process_id: str
    user_id: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> CodingAgentImplementationStarted:
        return CodingAgentImplementationStarted(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            user_id=self.user_id,
        )

    @classmethod
    def create_from(cls, event: CodingAgentImplementationStarted) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            user_id=event.user_id,
        )


class CodingAgentImplementationCompletedRecord(BaseModel):
    type: Literal["coding_agent_implementation_completed"] = "coding_agent_implementation_completed"
    occurred_at: datetime
    knowledge_base_id: str
    process_id: str
    user_id: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> CodingAgentImplementationCompleted:
        return CodingAgentImplementationCompleted(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            user_id=self.user_id,
        )

    @classmethod
    def create_from(cls, event: CodingAgentImplementationCompleted) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            user_id=event.user_id,
        )


class CodingAgentImplementationFailedRecord(BaseModel):
    type: Literal["coding_agent_implementation_failed"] = "coding_agent_implementation_failed"
    occurred_at: datetime
    knowledge_base_id: str
    process_id: str
    user_id: str
    error_type: str
    error_message: str

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> CodingAgentImplementationFailed:
        return CodingAgentImplementationFailed(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            user_id=self.user_id,
            error_type=self.error_type,
            error_message=self.error_message,
        )

    @classmethod
    def create_from(cls, event: CodingAgentImplementationFailed) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            user_id=event.user_id,
            error_type=event.error_type,
            error_message=event.error_message,
        )


ProcessTimelineEventRecords = (
    CodeRepositoryConnectedRecord
    | CodeRepositoryIntegrationFailedRecord
    | CodeRepositoryIndexedRecord
    | RepositoryIndexationRequestedRecord
    | CodingAgentRequestedRecord
    | CodingAgentImplementationStartedRecord
    | CodingAgentImplementationCompletedRecord
    | CodingAgentImplementationFailedRecord
    | PullRequestCreatedRecord
)


def obfuscate(secret: str) -> str:
    return "*" * (len(secret) - 4) + secret[-4:]


def serialize(event: AnyDomainEvent) -> ProcessTimelineEventRecords:
    match event:
        case CodeRepositoryConnected():
            return CodeRepositoryConnectedRecord.create_from(event)
        case CodeRepositoryIntegrationFailed():
            return CodeRepositoryIntegrationFailedRecord.create_from(event)
        case CodeRepositoryIndexed():
            return CodeRepositoryIndexedRecord.create_from(event)
        case RepositoryIndexationRequested():
            return RepositoryIndexationRequestedRecord.create_from(event)
        case CodingAgentRequested():
            return CodingAgentRequestedRecord.create_from(event)
        case CodingAgentImplementationStarted():
            return CodingAgentImplementationStartedRecord.create_from(event)
        case CodingAgentImplementationCompleted():
            return CodingAgentImplementationCompletedRecord.create_from(event)
        case _:
            assert_never(event)


def deserialize(event_type: str, data: str) -> AnyDomainEvent:
    match event_type:
        case "repository_connected":
            return CodeRepositoryConnectedRecord.model_validate_json(
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
        case "coding_agent_requested":
            return CodingAgentRequestedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "coding_agent_implementation_started":
            return CodingAgentImplementationStartedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "coding_agent_implementation_completed":
            return CodingAgentImplementationCompletedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "coding_agent_implementation_failed":
            return CodingAgentImplementationFailedRecord.model_validate_json(
                data
            ).to_domain_event()
        case "pull_request_created":
            return PullRequestCreatedRecord.model_validate_json(
                data
            ).to_domain_event()
        case _:
            raise Exception(f"Unknown event type: {event_type}")
