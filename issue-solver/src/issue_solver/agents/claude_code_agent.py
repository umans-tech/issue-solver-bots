import os
import logging
from pathlib import Path
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
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


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


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
        options = ClaudeAgentOptions(
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
                            logger.info("Claude: %s", block.text)
                        elif isinstance(block, ToolUseBlock):
                            logger.info(
                                "Tool Use: %s - id:%s - input: %s",
                                block.name,
                                block.id,
                                block.input,
                            )
                        elif isinstance(block, ToolResultBlock):
                            logger.info(
                                "Tool Result: %s - id: %s - output: %s",
                                block.is_error,
                                block.tool_use_id,
                                block.content,
                            )

                elif isinstance(message, ResultMessage):
                    if (
                        message.total_cost_usd is not None
                        and message.total_cost_usd > 0
                    ):
                        logger.info("Cost: $%.4f", message.total_cost_usd)
                elif isinstance(message, UserMessage):
                    logger.info("User: %s", message.content)
                elif isinstance(message, SystemMessage):
                    logger.info("System: %s - data: %s", message.subtype, message.data)

        except Exception as e:
            logger.error("Claude Code agent failed: %s", e)
            raise RuntimeError(f"Claude Code agent failed: {str(e)}", e)
