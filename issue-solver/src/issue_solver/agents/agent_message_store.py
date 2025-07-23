import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict

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


def get_messages_channel(process_id):
    return f"process:{process_id}:messages"


class StreamingAgentMessageStore(AgentMessageStore):
    def __init__(self, message_store: AgentMessageStore, redis_client) -> None:
        super().__init__()
        self.redis_client = redis_client
        self.message_store = message_store

    async def append(
        self, process_id: str, model: VersionedAIModel, turn: int, message, agent
    ) -> str:
        message_id = await self.message_store.append(
            process_id, model, turn, message, agent
        )
        agent_message = AgentMessage(
            id=message_id,
            type=message.__class__.__name__,
            turn=turn,
            agent=agent,
            model=model,
            payload=asdict(message),
        )

        self.redis_client.publish(
            get_messages_channel(process_id), json.dumps(asdict(agent_message))
        )

        return message_id

    async def get(self, process_id) -> list[AgentMessage]:
        return await self.message_store.get(process_id)
