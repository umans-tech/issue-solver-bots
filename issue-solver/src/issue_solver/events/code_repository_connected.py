from dataclasses import dataclass
from datetime import datetime, UTC

from issue_solver.events.domain_event import DomainEvent


@dataclass(frozen=True, slots=True)
class CodeRepositoryConnected(DomainEvent):
    url: str
    access_token: str
    user_id: str
    knowledge_base_id: str
    process_id: str
    occurred_at: datetime = datetime.now(UTC)
