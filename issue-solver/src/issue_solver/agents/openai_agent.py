import json

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

    async def run_full_turn(self, system_message, messages, model=None) -> TurnOutput:
        response = self.client.chat.completions.create(
            model=model if model else self.default_model,
            messages=[{"role": "system", "content": system_message}] + messages,
            tools=self.tools,
        )
        chat_completion_message: ChatCompletionMessage = response.choices[0].message
        messages.append(chat_completion_message)

        if chat_completion_message.tool_calls:
            function_call = chat_completion_message.tool_calls[0]
            function_name = function_call.function.name
            arguments = json.loads(function_call.function.arguments)
            tool_id = function_call.id

            tool_result = await self.tool_collection.run(
                name=function_name, tool_input=arguments
            )
            result_output = tool_result.output

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": function_name,
                    "content": result_output or tool_result.error,
                }
            )

        return OpenAITurnOutput(response.choices[0], messages)


class OpenAITurnOutput(TurnOutput):
    def __init__(self, chat_completion_choice: Choice, messages):
        self.chat_completion_choice = chat_completion_choice
        self.messages = messages

    def has_finished(self):
        return self.chat_completion_choice.finish_reason == "stop"

    def messages_history(self):
        return self.messages
