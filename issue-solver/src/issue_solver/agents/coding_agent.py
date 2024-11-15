from abc import ABC, abstractmethod

from issue_solver import AgentModel


class TurnOutput(ABC):
    @abstractmethod
    def has_finished(self) -> bool:
        pass

    @abstractmethod
    def messages_history(self):
        pass


class CodingAgent(ABC):
    @abstractmethod
    async def run_full_turn(
        self, system_message, messages, model: AgentModel | None = None
    ) -> TurnOutput:
        pass

    @abstractmethod
    async def process_tool_call(self, tool_name, tool_input):
        """Détermine et exécute le bon outil en fonction du nom."""
        pass
