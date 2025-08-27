from abc import ABC, abstractmethod
from collections import defaultdict
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


class InMemoryAgentMessageStore(AgentMessageStore):
    def __init__(self):
        self._messages = defaultdict(list)

    async def append(
        self, process_id: str, model: VersionedAIModel, turn: int, message, agent: str
    ) -> str:
        if process_id not in self._messages:
            self._messages[process_id] = []
        self._messages[process_id].append(message)
        return "message-id"

    async def get(self, process_id) -> list[AgentMessage]:
        self._messages = getattr(self, "_messages", {})
        return self._messages.get(process_id, [])
