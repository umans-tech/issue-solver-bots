import json
from dataclasses import asdict

from issue_solver.agents.agent_message_store import AgentMessageStore
from issue_solver.models.supported_models import VersionedAIModel


class PostgresAgentMessageStore(AgentMessageStore):
    def __init__(self, connection):
        self.connection = connection

    async def append(
        self, process_id: str, model: VersionedAIModel, turn: int, message
    ):
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
                gen_random_uuid(),
                $1,
                $2,
                $3,
                $4,
                $5,
                $6,
                CURRENT_TIMESTAMP
            )
            """,
            process_id,
            "CLAUDE_CODE",
            str(model),
            turn,
            json.dumps(asdict(message)),
            message.__class__.__name__,
        )

    async def get(self, process_id: str) -> list[dict]:
        rows = await self.connection.fetch(
            """
            SELECT message_id, process_id, agent, model, turn, message, message_type, created_at
            FROM agent_message_store
            WHERE process_id = $1
            ORDER BY turn ASC
            """,
            process_id,
        )

        messages = []
        for row in rows:
            messages.append(
                {
                    "message_id": row["message_id"],
                    "process_id": row["process_id"],
                    "agent": row["agent"],
                    "model": row["model"],
                    "turn": row["turn"],
                    "message": json.loads(row["message"]),
                    "message_type": row["message_type"],
                    "created_at": row["created_at"],
                }
            )
        return messages
