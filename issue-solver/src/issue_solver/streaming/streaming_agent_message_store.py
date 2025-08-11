import json
from dataclasses import asdict

import asyncpg
from redis import Redis

from issue_solver.agents.agent_message_store import AgentMessageStore, AgentMessage
from issue_solver.database.postgres_agent_message_store import PostgresAgentMessageStore
from issue_solver.models.supported_models import VersionedAIModel


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


async def init_agent_message_store(
    database_url: str | None, redis_url: str | None
) -> AgentMessageStore | None:
    if database_url and redis_url:
        agent_message_store = StreamingAgentMessageStore(
            PostgresAgentMessageStore(
                connection=await asyncpg.connect(
                    database_url.replace("+asyncpg", ""),
                    statement_cache_size=0,
                )
            ),
            redis_client=Redis.from_url(redis_url),
        )
        return agent_message_store
    return None
