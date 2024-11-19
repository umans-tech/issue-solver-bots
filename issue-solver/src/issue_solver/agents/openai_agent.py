import json
from typing import Any

from openai import OpenAI
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from issue_solver import AgentModel
from issue_solver.agents.coding_agent import TurnOutput, CodingAgent
from issue_solver.agents.tools.bash import BashTool
from issue_solver.agents.tools.collection import ToolCollection
from issue_solver.agents.tools.edit import EditTool
from issue_solver.agents.tools.openai_tools_schema import (
    bash_tool_schema,
    edit_tool_schema,
)


class OpenAIAgent(CodingAgent):
    def __init__(
        self,
        api_key: str,
        default_model: AgentModel = AgentModel.GPT4O_MINI,
        base_url: str | None = None,
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.default_model = default_model
        self.tools = [
            {"type": "function", "function": bash_tool_schema()},
            {"type": "function", "function": edit_tool_schema()},
        ]
        self.tool_collection = ToolCollection(BashTool(), EditTool())

    async def run_full_turn(
        self, system_message: str, messages: list[dict[str, Any]], model=None
    ) -> TurnOutput:
        response = self.client.chat.completions.create(
            model=model if model else self.default_model,
            messages=[{"role": "system", "content": system_message}] + messages,
            tools=self.tools,
        )
        chat_completion_message: ChatCompletionMessage = response.choices[0].message
        turn_output = OpenAITurnOutput(response.choices[0], messages)

        if chat_completion_message.tool_calls:
            for function_call in chat_completion_message.tool_calls:
                await self.use_tool(function_call, turn_output)

        return turn_output

    async def use_tool(self, function_call, turn_output: "OpenAITurnOutput"):
        function_name = function_call.function.name
        arguments = json.loads(function_call.function.arguments)
        tool_id = function_call.id
        tool_result = await self.tool_collection.run(
            name=function_name, tool_input=arguments
        )
        result_output = tool_result.output
        turn_output.append(
            {
                "role": "tool",
                "tool_call_id": tool_id,
                "name": function_name,
                "content": result_output or tool_result.error,
            }
        )


class OpenAITurnOutput(TurnOutput):
    def __init__(self, chat_completion_choice: Choice, messages):
        self.chat_completion_choice = chat_completion_choice
        chat_completion_message: ChatCompletionMessage = chat_completion_choice.message
        reasoning_message = {
            "role": chat_completion_message.role,
            "tool_calls": [
                one_tool_call.model_dump()
                for one_tool_call in chat_completion_message.tool_calls
            ]
            if chat_completion_message.tool_calls
            else [],
            "content": chat_completion_message.content or "",
        }
        self._messages_history = messages
        self._messages_history.append(reasoning_message)
        self._turn_messages = [reasoning_message]

    def append(self, message: dict[str, Any]) -> None:
        self._messages_history.append(message)
        self._turn_messages.append(message)

    def turn_messages(self) -> list[dict[str, Any]]:
        return self._turn_messages

    def has_finished(self):
        return self.chat_completion_choice.finish_reason == "stop"

    def messages_history(self):
        return self._messages_history
