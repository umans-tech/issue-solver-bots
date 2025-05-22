from typing import cast, Any

import anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolResultBlockParam

from issue_solver.agents.coding_agent import TurnOutput, CodingAgent, Message
from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    ResolveIssueCommand,
)
from issue_solver.agents.resolution_approaches import resolution_approach_prompt
from issue_solver.agents.tools.anthropic_tools_schema import bash_tool, edit_tool
from issue_solver.agents.tools.base import ToolResult
from issue_solver.agents.tools.bash import BashTool
from issue_solver.agents.tools.collection import ToolCollection
from issue_solver.agents.tools.edit import EditTool
from issue_solver.models.supported_models import (
    SupportedAnthropicModel,
    QualifiedAIModel,
)


class AnthropicAgent(
    CodingAgent[SupportedAnthropicModel, MessageParam], IssueResolvingAgent
):
    async def resolve_issue(self, command: ResolveIssueCommand) -> None:
        repo_location = command.repo_path
        issue_description = command.issue.description
        max_turns = 100

        system_message = resolution_approach_prompt(
            location=str(repo_location), pr_description=issue_description
        )
        if not isinstance(command.model.ai_model, SupportedAnthropicModel):
            raise ValueError(
                f"Unsupported model type: {command.model}. Supported models are: {SupportedAnthropicModel}"
            )
        has_finished = False
        turn = 1
        history: list[MessageParam | Message] = []
        while not has_finished:
            agent = self
            response = await agent.run_full_turn(
                system_message=system_message,
                messages=history,
                model=cast(QualifiedAIModel[SupportedAnthropicModel], command.model),
            )
            print(f"Turn {turn}: {response.turn_messages()}")
            turn += 1
            history = response.messages_history()  # type: ignore
            has_finished = response.has_finished() or turn == max_turns
        if not has_finished:
            raise Exception(f"Could not resolve issue in {turn} iterations")

    def __init__(
        self,
        api_key: str,
        default_model: QualifiedAIModel[SupportedAnthropicModel] = QualifiedAIModel(
            ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU, version="latest"
        ),
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
        self.tool_collection = ToolCollection(BashTool(), EditTool())

    async def run_full_turn(
        self,
        system_message: str,
        messages: list[MessageParam | Message],
        model: QualifiedAIModel[SupportedAnthropicModel] | None = None,
    ) -> TurnOutput[MessageParam]:
        history = [to_agent_message(one_message) for one_message in messages]
        reasoning_response = self.client.messages.create(
            model=str(model) or str(self.default_model),
            max_tokens=4096,
            messages=[MessageParam(role="user", content=system_message)] + history,
            tools=self.tools,
        )
        turn_output = AnthropicTurnOutput(reasoning_response, history)

        if reasoning_response.stop_reason == "tool_use":
            tool_use = next(
                block
                for block in reasoning_response.content
                if block.type == "tool_use"
            )
            tool_name = tool_use.name
            tool_input = cast(dict[str, Any], tool_use.input)

            tool_result = await self.tool_collection.run(
                name=tool_name, tool_input=tool_input
            )

            tool_result_content = _make_api_tool_result(tool_result, tool_use.id)

            turn_output.append(
                MessageParam(
                    role="user",
                    content=[tool_result_content],
                )
            )

        return turn_output


def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> ToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    if result.error:
        return ToolResultBlockParam(
            type="tool_result",
            content=_maybe_prepend_system_tool_result(result, result.error),
            tool_use_id=tool_use_id,
            is_error=True,
        )

    tool_result_content: list[TextBlockParam] = []
    if result.output:
        tool_result_content.append(
            TextBlockParam(
                type="text",
                text=_maybe_prepend_system_tool_result(result, result.output),
            )
        )
    return ToolResultBlockParam(
        type="tool_result",
        content=tool_result_content,
        tool_use_id=tool_use_id,
        is_error=False,
    )


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str) -> str:
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text


class AnthropicTurnOutput(TurnOutput[MessageParam]):
    def __init__(
        self,
        reasoning_response: anthropic.types.message.Message,
        messages: list[MessageParam],
    ):
        self.reasoning_response = reasoning_response

        reasoning_message = MessageParam(
            role=reasoning_response.role,
            content=reasoning_response.content,
        )
        self._messages_history = messages
        self._messages_history.append(reasoning_message)
        self._turn_messages = [reasoning_message]

    def append(self, message: MessageParam) -> None:
        self._turn_messages.append(message)
        self._messages_history.append(message)

    def turn_messages(self) -> list[MessageParam]:
        return self._turn_messages

    def has_finished(self) -> bool:
        return self.reasoning_response.stop_reason == "end_turn"

    def messages_history(self) -> list[MessageParam]:
        return self._messages_history


def to_agent_message(
    one_message: MessageParam | Message,
) -> MessageParam:
    if isinstance(one_message, Message):
        return MessageParam(
            role="user" if one_message.role == "user" else "assistant",
            content=one_message.content,
        )
    else:
        return one_message
