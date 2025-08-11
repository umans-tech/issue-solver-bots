import json
from typing import assert_never

import openai
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from issue_solver.agents.coding_agent import TurnOutput, CodingAgent, Message
from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    ResolveIssueCommand,
)
from issue_solver.agents.tools.bash import BashTool
from issue_solver.agents.tools.collection import ToolCollection
from issue_solver.agents.tools.edit import EditTool
from issue_solver.agents.tools.openai_tools_schema import (
    bash_tool_schema,
    edit_tool_schema,
)
from issue_solver.models.supported_models import (
    SupportedOpenAIModel,
    QualifiedAIModel,
)


class OpenAIAgent(
    CodingAgent[SupportedOpenAIModel, ChatCompletionMessageParam], IssueResolvingAgent
):
    async def resolve_issue(self, command: ResolveIssueCommand) -> None:
        pass

    def __init__(
        self,
        api_key: str,
        default_model: QualifiedAIModel[SupportedOpenAIModel] = QualifiedAIModel(
            ai_model=SupportedOpenAIModel.GPT4O_MINI
        ),
        base_url: str | None = None,
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.default_model = default_model
        self.tools = [
            ChatCompletionToolParam(type="function", function=bash_tool_schema()),
            ChatCompletionToolParam(type="function", function=edit_tool_schema()),
        ]
        self.tool_collection = ToolCollection(BashTool(), EditTool())

    async def run_full_turn(
        self,
        system_message: str,
        messages: list[ChatCompletionMessageParam | Message],
        model: QualifiedAIModel[SupportedOpenAIModel] | None = None,
    ) -> TurnOutput[ChatCompletionMessageParam]:
        history = [to_agent_message(message) for message in messages]
        all_messages = [
            ChatCompletionSystemMessageParam(role="system", content=system_message)
        ] + history

        response = self.client.chat.completions.create(
            model=str(model) or str(self.default_model),
            messages=all_messages,
            tools=self.tools,
        )
        chat_completion_message: ChatCompletionMessage = response.choices[0].message
        turn_output = OpenAITurnOutput(response.choices[0], history)

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
            ChatCompletionToolMessageParam(
                role="tool",
                tool_call_id=tool_id,
                content=result_output or tool_result.error or "missing output",
            )
        )


def to_agent_message(
    message: ChatCompletionMessageParam | Message,
) -> ChatCompletionMessageParam:
    if isinstance(message, Message):
        match message.role:
            case "system":
                return ChatCompletionSystemMessageParam(
                    content=message.content, role="system"
                )
            case "user":
                return ChatCompletionUserMessageParam(
                    content=message.content, role="user"
                )
            case "assistant":
                return ChatCompletionAssistantMessageParam(
                    content=message.content, role="assistant"
                )
            case "tool":
                return ChatCompletionToolMessageParam(
                    content=message.content, role="tool", tool_call_id=""
                )
            case "function":
                return ChatCompletionFunctionMessageParam(
                    content=message.content, role="function", name=""
                )
            case _:
                assert_never(message.role)
    return message


class OpenAITurnOutput(TurnOutput[ChatCompletionMessageParam]):
    def __init__(
        self, chat_completion_choice: Choice, messages: list[ChatCompletionMessageParam]
    ):
        self.chat_completion_choice = chat_completion_choice
        chat_completion_message: ChatCompletionMessage = chat_completion_choice.message
        reasoning_message: ChatCompletionAssistantMessageParam = {
            "role": chat_completion_message.role,
            "tool_calls": [
                convert_tool_call_param(one_tool_call)
                for one_tool_call in chat_completion_message.tool_calls
            ]
            if chat_completion_message.tool_calls
            else [],
            "content": chat_completion_message.content or "",
        }
        self._messages_history = messages
        self._messages_history.append(reasoning_message)
        self._turn_messages: list[ChatCompletionMessageParam] = [reasoning_message]

    def append(self, message: ChatCompletionMessageParam) -> None:
        self._messages_history.append(message)
        self._turn_messages.append(message)

    def turn_messages(self) -> list[ChatCompletionMessageParam]:
        return self._turn_messages

    def has_finished(self) -> bool:
        return self.chat_completion_choice.finish_reason == "stop"

    def messages_history(self) -> list[ChatCompletionMessageParam]:
        return self._messages_history


def convert_tool_call_function(
    func: openai.types.chat.chat_completion_message_tool_call.Function,
) -> openai.types.chat.chat_completion_message_tool_call_param.Function:
    return {
        "name": func.name,
        "arguments": func.arguments,
    }


def convert_tool_call_param(
    one_tool_call: ChatCompletionMessageToolCall,
) -> ChatCompletionMessageToolCallParam:
    return {
        "id": one_tool_call.id,
        "function": convert_tool_call_function(one_tool_call.function),
        "type": one_tool_call.type,
    }
