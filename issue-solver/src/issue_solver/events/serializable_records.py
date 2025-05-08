from datetime import datetime
from typing import Any, Literal, Self, Type, assert_never

from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryIntegrationFailed,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    T,
    IssueResolutionRequested,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    IssueResolutionFailed,
)
from pydantic import BaseModel

from issue_solver.issues.issue import IssueInfo


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

    def safe_copy(self) -> Self:
        return self.model_copy()

    def to_domain_event(self) -> IssueResolutionRequested:
        return IssueResolutionRequested(
            occurred_at=self.occurred_at,
            knowledge_base_id=self.knowledge_base_id,
            process_id=self.process_id,
            issue=self.issue,
        )

    @classmethod
    def create_from(cls, event: IssueResolutionRequested) -> Self:
        return cls(
            occurred_at=event.occurred_at,
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
            issue=event.issue,
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


ProcessTimelineEventRecords = (
    CodeRepositoryConnectedRecord
    | CodeRepositoryIntegrationFailedRecord
    | CodeRepositoryIndexedRecord
    | RepositoryIndexationRequestedRecord
    | IssueResolutionRequestedRecord
    | IssueResolutionStartedRecord
    | IssueResolutionCompletedRecord
    | IssueResolutionFailedRecord
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
        case IssueResolutionRequested():
            return IssueResolutionRequestedRecord.create_from(event)
        case IssueResolutionStarted():
            return IssueResolutionStartedRecord.create_from(event)
        case IssueResolutionCompleted():
            return IssueResolutionCompletedRecord.create_from(event)
        case IssueResolutionFailed():
            return IssueResolutionFailedRecord.create_from(event)
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
        case _:
            raise Exception(f"Unknown event type: {event_type}")
