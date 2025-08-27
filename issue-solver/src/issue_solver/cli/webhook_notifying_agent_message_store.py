from dataclasses import asdict

import httpx

from issue_solver.agents.agent_message_store import AgentMessageStore, AgentMessage
from issue_solver.models.supported_models import VersionedAIModel
from issue_solver.webapi.payloads import AgentMessageNotification


class WebhookNotifyingAgentMessageStore(AgentMessageStore):
    def __init__(
        self, store: AgentMessageStore, messages_webhook_url: str, http_client=httpx
    ):
        self.http_client = http_client
        self.store = store
        self.messages_webhook_url = messages_webhook_url

    async def append(
        self, process_id: str, model: VersionedAIModel, turn: int, message, agent: str
    ) -> str:
        stored_message_id = await self.store.append(
            process_id, model, turn, message, agent
        )
        self.http_client.post(
            url=self.messages_webhook_url,
            json=AgentMessageNotification(
                process_id=process_id,
                agent_message=AgentMessage(
                    id=stored_message_id,
                    payload=message if isinstance(message, dict) else asdict(message),
                    model=model,
                    turn=turn,
                    agent=agent,
                    type=message.__class__.__name__,
                ),
            ).model_dump(mode="json"),
        )
        return stored_message_id

    async def get(self, process_id) -> list[AgentMessage]:
        return await self.store.get(process_id)
