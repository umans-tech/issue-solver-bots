import os
from pathlib import Path
from typing import Optional, Literal, Any, Dict, Union
import logging

from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk.types import (
    UserMessage as ClaudeCodeUserMessage,
    AssistantMessage as ClaudeCodeAssistantMessage,
    SystemMessage as ClaudeCodeSystemMessage,
    ResultMessage as ClaudeCodeResultMessage,
)

from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    ResolveIssueCommand,
)
from issue_solver.agents.coding_agent import CodingAgent, TurnOutput, Message
from issue_solver.models.supported_models import (
    SupportedAnthropicModel,
    QualifiedAIModel,
)

logger = logging.getLogger()

# Type alias for Claude Code message types
ClaudeCodeMessage = Union[
    ClaudeCodeUserMessage,
    ClaudeCodeAssistantMessage,
    ClaudeCodeSystemMessage,
    ClaudeCodeResultMessage,
]


class ClaudeCodeAgent(
    CodingAgent[SupportedAnthropicModel, Message], IssueResolvingAgent
):
    """
    Claude Code agent that uses Anthropic's Claude Code SDK to resolve issues.
    This agent runs Claude Code as a subprocess and provides comprehensive
    IDE-like capabilities including file operations, bash commands, and code analysis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_turns: int = 100,
        permission_mode: Literal[
            "default", "acceptEdits", "bypassPermissions"
        ] = "acceptEdits",
    ):
        super().__init__()
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.max_turns = max_turns
        self.permission_mode = permission_mode

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required for Claude Code agent"
            )

    async def resolve_issue(self, command: ResolveIssueCommand) -> None:
        """
        Resolve an issue using Claude Code SDK.

        Args:
            command: ResolveIssueCommand containing issue details, repo path, and model info
        """
        # Set up environment for Claude Code
        original_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if self.api_key:
            os.environ["ANTHROPIC_API_KEY"] = self.api_key

        repo_path = Path(command.repo_path)
        logger.info(f"Resolving issue using Claude Code in {repo_path}")

        try:
            # Build comprehensive prompt for Claude Code
            issue_prompt = self._build_issue_prompt(command)

            # Configure Claude Code options
            options = ClaudeCodeOptions(
                max_turns=self.max_turns,
                cwd=repo_path,
                permission_mode=self.permission_mode,
                # Enable comprehensive toolset for code operations
                allowed_tools=["Read", "Write", "Bash", "Edit"],
            )

            # Run Claude Code to resolve the issue
            messages: list[ClaudeCodeMessage] = []
            async for message in query(prompt=issue_prompt, options=options):
                messages.append(message)
                # Log progress
                message_type = self._get_message_type(message)
                logger.info(f"Claude Code message type: {message_type}")

            # Validate successful completion
            if not messages:
                raise Exception("Claude Code produced no output")

            final_result = messages[-1]
            if self._get_message_type(final_result) != "result":
                raise Exception("Claude Code did not complete with a result message")

            if self._get_message_error_status(final_result):
                error_msg = (
                    self._get_message_result(final_result) or "Unknown error occurred"
                )
                raise Exception(f"Claude Code execution failed: {error_msg}")

            # Log success metrics
            duration_ms = self._get_message_duration(final_result)
            num_turns = self._get_message_turns(final_result)
            cost_usd = self._get_message_cost(final_result)
            logger.info(
                f"Claude Code completed successfully: {num_turns} turns, "
                f"{duration_ms}ms duration, ${cost_usd:.4f} cost"
            )

        except Exception as e:
            logger.error(f"Claude Code agent failed: {str(e)}")
            raise Exception(f"Claude Code agent execution failed: {str(e)}")
        finally:
            # Restore original API key
            if original_api_key is not None:
                os.environ["ANTHROPIC_API_KEY"] = original_api_key
            elif "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

    def _get_message_type(self, message: ClaudeCodeMessage) -> str:
        """Extract message type from Claude Code message."""
        if isinstance(message, ClaudeCodeUserMessage):
            return "user"
        elif isinstance(message, ClaudeCodeAssistantMessage):
            return "assistant"
        elif isinstance(message, ClaudeCodeSystemMessage):
            return "system"
        elif isinstance(message, ClaudeCodeResultMessage):
            return "result"
        else:
            return "unknown"

    def _get_message_error_status(self, message: ClaudeCodeMessage) -> bool:
        """Extract error status from Claude Code message."""
        if hasattr(message, "is_error"):
            return bool(getattr(message, "is_error", False))
        return False

    def _get_message_result(self, message: ClaudeCodeMessage) -> Optional[str]:
        """Extract result from Claude Code message."""
        if hasattr(message, "result"):
            result = getattr(message, "result", None)
            return str(result) if result is not None else None
        return None

    def _get_message_duration(self, message: ClaudeCodeMessage) -> int:
        """Extract duration from Claude Code message."""
        if hasattr(message, "duration_ms"):
            return int(getattr(message, "duration_ms", 0))
        return 0

    def _get_message_turns(self, message: ClaudeCodeMessage) -> int:
        """Extract number of turns from Claude Code message."""
        if hasattr(message, "num_turns"):
            return int(getattr(message, "num_turns", 0))
        return 0

    def _get_message_cost(self, message: ClaudeCodeMessage) -> float:
        """Extract cost from Claude Code message."""
        if hasattr(message, "total_cost_usd"):
            return float(getattr(message, "total_cost_usd", 0.0))
        return 0.0

    def _build_issue_prompt(self, command: ResolveIssueCommand) -> str:
        """
        Build a comprehensive prompt for Claude Code to resolve the issue.

        Args:
            command: ResolveIssueCommand with issue details

        Returns:
            Formatted prompt string for Claude Code
        """
        issue = command.issue
        repo_path = command.repo_path

        prompt_parts = [
            f"I need you to resolve the following issue in the codebase located at {repo_path}:",
            "",
        ]

        if issue.title:
            prompt_parts.extend(
                [
                    f"**Issue Title:** {issue.title}",
                    "",
                ]
            )

        prompt_parts.extend(
            [
                "**Issue Description:**",
                issue.description,
            ]
        )

        return "\n".join(prompt_parts)

    async def run_full_turn(
        self,
        system_message: str,
        messages: list[Message],
        model: QualifiedAIModel[SupportedAnthropicModel] | None = None,
    ) -> TurnOutput[Message]:
        """
        Run a full turn using Claude Code SDK.
        This method is required by CodingAgent interface but delegates to Claude Code's internal handling.
        """
        # Claude Code handles turns internally, so we simulate a single turn
        # by running the system message as a prompt
        options = ClaudeCodeOptions(
            max_turns=1,  # Single turn for this method
            cwd=Path.cwd(),
            permission_mode=self.permission_mode,
            allowed_tools=["Read", "Write", "Bash", "Edit"],
        )

        response_messages: list[ClaudeCodeMessage] = []
        try:
            async for message in query(prompt=system_message, options=options):
                response_messages.append(message)
        except Exception as e:
            # Return a failed turn output
            return ClaudeCodeTurnOutput([], has_error=True, error_message=str(e))

        # Convert Claude Code messages to dict format for ClaudeCodeTurnOutput
        message_dicts = [self._claude_message_to_dict(msg) for msg in response_messages]
        return ClaudeCodeTurnOutput(message_dicts)

    def _claude_message_to_dict(self, message: ClaudeCodeMessage) -> Dict[str, Any]:
        """Convert Claude Code message to dict format."""
        base_dict: Dict[str, Any] = {"type": self._get_message_type(message)}

        # Add message content if available
        if hasattr(message, "message"):
            base_dict["message"] = getattr(message, "message")

        # Add additional fields for result messages
        if isinstance(message, ClaudeCodeResultMessage):
            base_dict["is_error"] = self._get_message_error_status(message)
            base_dict["result"] = self._get_message_result(message)
            base_dict["duration_ms"] = self._get_message_duration(message)
            base_dict["num_turns"] = self._get_message_turns(message)
            base_dict["total_cost_usd"] = self._get_message_cost(message)

        return base_dict


class ClaudeCodeTurnOutput(TurnOutput[Message]):
    """Turn output wrapper for Claude Code responses."""

    def __init__(
        self,
        messages: list[Dict[str, Any]],
        has_error: bool = False,
        error_message: str = "",
    ):
        self._messages = messages
        self._has_error = has_error
        self._error_message = error_message

    def has_finished(self) -> bool:
        """Check if the turn has finished successfully."""
        if self._has_error:
            return True
        if not self._messages:
            return False
        last_message = self._messages[-1]
        return last_message.get("type") == "result" and not last_message.get(
            "is_error", False
        )

    def messages_history(self) -> list[Message]:
        """Return the message history as Message objects."""
        history = []
        for msg in self._messages:
            if msg.get("type") == "assistant":
                history.append(
                    Message(role="assistant", content=str(msg.get("message", "")))
                )
            elif msg.get("type") == "user":
                history.append(
                    Message(role="user", content=str(msg.get("message", "")))
                )
        return history

    def append(self, message: Message) -> None:
        """Append a message to the history."""
        # Convert Message to dict format
        self._messages.append(
            {
                "type": "user" if message.role == "user" else "assistant",
                "message": message.content,
            }
        )

    def turn_messages(self) -> list[Message]:
        """Return messages from this turn only."""
        return self.messages_history()
