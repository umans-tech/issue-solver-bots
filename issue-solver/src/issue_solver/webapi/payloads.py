from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from pydantic.alias_generators import to_camel

from issue_solver.agents.agent_message_store import AgentMessage
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.env_setup.dev_environments_management import (
    ExecutionEnvironmentPreference,
)
from issue_solver.issues.issue import IssueInfo
from issue_solver.models.supported_models import (
    SupportedAIModel,
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_VERSION,
)


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ConnectRepositoryRequest(BaseSchema):
    url: str
    access_token: str
    space_id: str = Field(default="")


class RotateTokenRequest(BaseSchema):
    access_token: str


class ResolveIssueRequest(BaseSchema):
    knowledge_base_id: str
    issue: IssueInfo
    agent: SupportedAgent = SupportedAgent.CLAUDE_CODE
    max_turns: int = 100
    ai_model: SupportedAIModel = SupportedAnthropicModel.CLAUDE_SONNET_4
    ai_model_version: str | None = LATEST_CLAUDE_4_VERSION
    execution_environment: ExecutionEnvironmentPreference = (
        ExecutionEnvironmentPreference.ENV_PREFERRED
    )


class ProcessCreated(BaseSchema):
    process_id: str


class EnvironmentConfiguration(BaseSchema):
    global_setup: str | None = Field(
        default=None,
        description="Global setup script. This will be run once per environment from root directory. Useful for installing system packages and dependencies.",
        validation_alias=AliasChoices(
            "global",
        ),
    )
    project_setup: str = Field(
        description="Project setup script. This will be run once per project from the project directory (after cloning). Useful for installing project specific dependencies.",
        validation_alias=AliasChoices(
            "project",
            "script",
        ),
    )


class AgentMessageNotification(BaseSchema):
    process_id: str
    agent_message: AgentMessage
