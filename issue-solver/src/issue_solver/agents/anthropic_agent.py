from typing import cast, Any

import anthropic

from issue_solver import AgentModel
from issue_solver.agents.anthropic_tools.base import ToolError, ToolFailure, ToolResult
from issue_solver.agents.anthropic_tools.bash import BashTool
from issue_solver.agents.anthropic_tools.edit import EditTool
from issue_solver.agents.anthropic_tools.tool_schema import bash_tool, edit_tool
from issue_solver.agents.coding_agent import TurnOutput, CodingAgent


class AnthropicAgent(CodingAgent):
    def __init__(
            self,
            api_key: str,
            default_model=AgentModel.CLAUDE_35_HAIKU,
            base_url: str | None = None,
    ):
        super().__init__()
        self.api_key = api_key
        self.default_model = default_model
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.tools = [
            bash_tool(),
            edit_tool(),
        ]

    async def run_full_turn(
            self, system_message, messages, model: AgentModel | None = None
    ) -> TurnOutput:
        reasoning_response: anthropic.types.message.Message = (
            self.client.messages.create(
                model=model or self.default_model,
                max_tokens=4096,
                messages=[
                             {
                                 "role": "user",
                                 "content": system_message,
                             }
                         ]
                         + messages,
                tools=self.tools,
            )
        )
        if reasoning_response.stop_reason == "tool_use":
            tool_use = next(
                block
                for block in reasoning_response.content
                if block.type == "tool_use"
            )
            tool_name = tool_use.name
            tool_input = cast(dict[str, Any], tool_use.input)

            messages.append(
                {"role": reasoning_response.role, "content": reasoning_response.content}
            )

            tool_result = await self.process_tool_call(tool_name, tool_input)

            tool_result_content = _make_api_tool_result(tool_result, tool_use.id)

            messages.append(
                {
                    "role": "user",
                    "content": [tool_result_content],
                }
            )

        return AnthropicTurnOutput(reasoning_response, messages)

    async def process_tool_call(self, tool_name, tool_input):
        try:
            if tool_name == "str_replace_editor":
                return await EditTool()(**tool_input)
            elif tool_name == "bash":
                return await BashTool()(**tool_input)
            else:
                return ToolFailure(error=f"Tool {tool_name} is invalid")
        except ToolError as e:
            return ToolFailure(error=e.message)


def _make_api_tool_result(result: ToolResult, tool_use_id: str):
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text


class AnthropicTurnOutput(TurnOutput):
    def __init__(self, reasoning_response: anthropic.types.message.Message, messages):
        self.reasoning_response = reasoning_response
        self.messages = messages

    def has_finished(self):
        return self.reasoning_response.stop_reason == "end_turn"

    def messages_history(self):
        return self.messages
