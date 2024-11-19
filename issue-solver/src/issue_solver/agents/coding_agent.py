from abc import ABC, abstractmethod
from typing import Any

from issue_solver import AgentModel


class TurnOutput(ABC):
    @abstractmethod
    def has_finished(self) -> bool:
        pass

    @abstractmethod
    def messages_history(self):
        pass

    @abstractmethod
    def append(self, message: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def turn_messages(self) -> list[dict[str, Any]]:
        pass


class CodingAgent(ABC):
    @abstractmethod
    async def run_full_turn(
        self,
        system_message: str,
        messages: list[dict[str, Any]],
        model: AgentModel | None = None,
    ) -> TurnOutput:
        pass
