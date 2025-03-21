from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel

from issue_solver.events.domain import CodeRepositoryConnected


class CodeRepositoryConnectedRecord(BaseModel):
    type: Literal["repository_connected"]
    occurred_at: datetime
    url: str
    access_token: str
    user_id: str
    space_id: str
    knowledge_base_id: str
    process_id: str

    @classmethod
    def create_from(cls, event: CodeRepositoryConnected) -> Self:
        return cls(
            type="repository_connected",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
            url=event.url,
            access_token=obfuscate(event.access_token),
            user_id=event.user_id,
            space_id="Todo: get space id",
            knowledge_base_id=event.knowledge_base_id,
            process_id=event.process_id,
        )


ProcessTimelineEventRecords = CodeRepositoryConnectedRecord


def obfuscate(secret: str) -> str:
    return "***********oken"
