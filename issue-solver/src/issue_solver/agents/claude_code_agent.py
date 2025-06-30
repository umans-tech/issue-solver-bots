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
from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    ResolveIssueCommand,
)


class ClaudeCodeAgent(IssueResolvingAgent):
    def __init__(self, api_key: str):
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
            allowed_tools=["Read", "Write", "Bash", "Edit"],
            permission_mode="bypassPermissions",
            system_prompt=f"You are a coding assistant. Resolve this issue: {issue_description}",
        )

        prompt = f"""
        Please analyze and resolve this issue in the repository:
        
        Issue: {issue_description}
        
        Repository location: {repo_location}
        
        Steps to follow:
        1. Explore the codebase to understand the structure
        2. Identify the root cause of the issue
        3. Implement the necessary changes
        4. Test your changes if possible
        """

        try:
            async for message in query(prompt=prompt, options=options):
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
