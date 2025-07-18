from abc import ABC, abstractmethod

from issue_solver.models.supported_models import VersionedAIModel


class AgentMessageStore(ABC):
    @abstractmethod
    async def append(
        self, process_id: str, model: VersionedAIModel, turn: int, message
    ):
        pass

    @abstractmethod
    async def get(self, process_id):
        pass
