from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Literal

from issue_solver.models.supported_models import ModelT, QualifiedAIModel


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool", "function"]
    content: str


MessageT = TypeVar("MessageT")


class TurnOutput(ABC, Generic[MessageT]):
    @abstractmethod
    def has_finished(self) -> bool:
        pass

    @abstractmethod
    def messages_history(self) -> list[MessageT]:
        pass

    @abstractmethod
    def append(self, message: MessageT) -> None:
        pass

    @abstractmethod
    def turn_messages(self) -> list[MessageT]:
        pass


class CodingAgent(ABC, Generic[ModelT, MessageT]):
    @abstractmethod
    async def run_full_turn(
        self,
        system_message: str,
        messages: list[MessageT | Message],
        model: QualifiedAIModel[ModelT] | None = None,
    ) -> TurnOutput[MessageT]:
        pass
