from abc import ABC, abstractmethod
from dataclasses import dataclass

from issue_solver.models.supported_models import VersionedAIModel


@dataclass
class AgentMessage:
    id: str
    type: str
    turn: int
    agent: str
    model: VersionedAIModel
    payload: dict


class AgentMessageStore(ABC):
    @abstractmethod
    async def append(
        self, process_id: str, model: VersionedAIModel, turn: int, message, agent: str
    ) -> str:
        pass

    @abstractmethod
    async def get(self, process_id) -> list[AgentMessage]:
        pass
