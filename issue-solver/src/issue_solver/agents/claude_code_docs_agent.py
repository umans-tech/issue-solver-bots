import os
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
from issue_solver.agents.docs_prompts import documenting_agent_system_prompt
from issue_solver.agents.issue_resolving_agent import (
    DocumentingAgent,
)
from issue_solver.models.supported_models import (
    QualifiedAIModel,
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_5_VERSION,
    VersionedAIModel,
)


class ClaudeCodeDocsAgent(DocumentingAgent):
    def __init__(
        self, api_key: str, agent_messages: AgentMessageStore | None = None
    ) -> None:
        self.agent_messages = agent_messages
        self.api_key = api_key
        os.environ["ANTHROPIC_API_KEY"] = api_key

    async def generate_documentation(
        self,
        repo_path: Path,
        knowledge_base_id: str,
        output_path: Path,
        docs_prompts: dict[str, str],
        process_id: str,
    ) -> None:
        repo_location = repo_path

        # Configure Claude Code options
        default_model: VersionedAIModel = QualifiedAIModel(
            ai_model=SupportedAnthropicModel.CLAUDE_SONNET_4_5,
            version=LATEST_CLAUDE_4_5_VERSION,
        )
        options = ClaudeAgentOptions(
            cwd=str(repo_location),
            model=str(default_model),
            max_turns=100,
            permission_mode="bypassPermissions",
            system_prompt=documenting_agent_system_prompt(output_path),
        )

        prompt = f"""
        Please generate the following documentation files in markdown format in the directory '{output_path}':
        
        Here is the list of documentation to generate:
        {"\n".join([f"- {name}: {desc}" for name, desc in docs_prompts.items()])}
        
        All files should be created in the '{output_path}' directory.
        
        """

        try:
            turn = 0
            async for message in query(prompt=prompt, options=options):
                turn += 1
                if self.agent_messages:
                    await self.agent_messages.append(
                        process_id, default_model, turn, message, "CLAUDE_CODE"
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
