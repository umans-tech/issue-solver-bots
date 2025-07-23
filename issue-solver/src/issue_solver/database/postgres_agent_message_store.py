import json
import uuid
from dataclasses import asdict

from issue_solver.agents.agent_message_store import AgentMessageStore, AgentMessage
from issue_solver.models.supported_models import VersionedAIModel


class PostgresAgentMessageStore(AgentMessageStore):
    def __init__(self, connection):
        self.connection = connection

    async def append(
        self, process_id: str, model: VersionedAIModel, turn: int, message, agent: str
    ) -> str:
        message_id = str(uuid.uuid4())
        await self.connection.execute(
            """
            INSERT INTO agent_message_store (message_id,
                                        process_id,
                                        agent,
                                        model,
                                        turn,
                                        message,
                                        message_type,
                                        created_at)
            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5,
                $6,
                $7,
                CURRENT_TIMESTAMP
            )
            """,
            message_id,
            process_id,
            agent,
            str(model),
            turn,
            json.dumps(asdict(message)),
            message.__class__.__name__,
        )
        return message_id

    async def get(self, process_id: str) -> list[AgentMessage]:
        rows = await self.connection.fetch(
            """
            SELECT message_id, process_id, agent, model, turn, message, message_type, created_at
            FROM agent_message_store
            WHERE process_id = $1
            ORDER BY turn ASC
            """,
            process_id,
        )

        messages: list[AgentMessage] = []
        for row in rows:
            messages.append(
                AgentMessage(
                    id=str(row["message_id"]),
                    type=row["message_type"],
                    turn=row["turn"],
                    agent=row["agent"],
                    model=row["model"],
                    payload=json.loads(row["message"]),
                )
            )
        return messages
