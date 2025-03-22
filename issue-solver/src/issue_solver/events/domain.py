from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True, frozen=True)
class DomainEvent(ABC):
    @property
    @abstractmethod
    def occurred_at(self) -> datetime:
        pass

    @property
    @abstractmethod
    def process_id(self) -> str:
        pass


@dataclass(frozen=True, slots=True)
class CodeRepositoryConnected(DomainEvent):
    url: str
    access_token: str
    user_id: str
    space_id: str
    knowledge_base_id: str
    process_id: str
    occurred_at: datetime


AnyDomainEvent = CodeRepositoryConnected
