import os
from pathlib import Path
from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    query,
    UserMessage,
    SystemMessage,
    ToolUseBlock,
    ToolResultBlock,
)

from issue_solver.agents.agent_message_store import AgentMessageStore
from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    ResolveIssueCommand,
)
from issue_solver.agents.resolution_approaches import (
    pragmatic_coding_agent_system_prompt,
)


class ClaudeCodeAgent(IssueResolvingAgent):
    def __init__(
        self, api_key: str, agent_messages: AgentMessageStore | None = None
    ) -> None:
        self.agent_messages = agent_messages
        self.api_key = api_key
        os.environ["ANTHROPIC_API_KEY"] = api_key

    async def resolve_issue(self, command: ResolveIssueCommand) -> None:
        repo_location = Path(command.repo_path)
        issue_description = command.issue.description

        # Configure Claude Code options
        options = ClaudeCodeOptions(
            cwd=str(repo_location),
            model=str(command.model),
            max_turns=100,
            permission_mode="bypassPermissions",
            system_prompt=pragmatic_coding_agent_system_prompt(),
        )

        prompt = f"""
        Please analyze and resolve this issue in the repository:
        
        Repository location: {repo_location}
        
        Issue: {command.issue.title}
        {issue_description}

        """

        try:
            turn = 0
            async for message in query(prompt=prompt, options=options):
                turn += 1
                if self.agent_messages:
                    await self.agent_messages.append(
                        command.process_id, command.model, turn, message, "CLAUDE_CODE"
                    )

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")
                        elif isinstance(block, ToolUseBlock):
                            print(
                                f"Tool Use: {block.name} - id:{block.id} - input: {block.input}"
                            )
                        elif isinstance(block, ToolResultBlock):
                            print(
                                f"Tool Result: {block.is_error} - id: {block.tool_use_id} - output: {block.content}"
                            )

                elif isinstance(message, ResultMessage):
                    if (
                        message.total_cost_usd is not None
                        and message.total_cost_usd > 0
                    ):
                        print(f"Cost: ${message.total_cost_usd:.4f}")
                elif isinstance(message, UserMessage):
                    print(f"User: {message.content}")
                elif isinstance(message, SystemMessage):
                    print(f"System: {message.subtype} - data: {message.data}")

        except Exception as e:
            raise RuntimeError(f"Claude Code agent failed: {str(e)}", e)
