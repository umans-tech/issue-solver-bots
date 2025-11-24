from datetime import datetime

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
    LATEST_CLAUDE_4_5_VERSION,
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


class NotionIntegrationView(BaseSchema):
    space_id: str
    process_id: str
    connected_at: datetime
    workspace_id: str | None = None
    workspace_name: str | None = None
    bot_id: str | None = None
    token_expires_at: datetime | None = None
    has_mcp_token: bool = False


class ResolveIssueRequest(BaseSchema):
    knowledge_base_id: str
    issue: IssueInfo
    agent: SupportedAgent = SupportedAgent.CLAUDE_CODE
    max_turns: int = 100
    ai_model: SupportedAIModel = SupportedAnthropicModel.CLAUDE_SONNET_4_5
    ai_model_version: str | None = LATEST_CLAUDE_4_5_VERSION
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


class AutoDocumentationConfigRequest(BaseSchema):
    docs_prompts: dict[str, str] = Field(
        description="Mapping between documentation identifiers and the prompts used to generate them",
        min_length=1,
    )


class AutoDocumentationDeleteRequest(BaseSchema):
    prompt_ids: set[str] = Field(
        description="Identifiers of documentation prompts to delete",
        min_length=1,
        validation_alias=AliasChoices("promptIds"),
    )


class AutoDocManualGenerationRequest(BaseSchema):
    prompt_id: str = Field(..., min_length=1, validation_alias=AliasChoices("promptId"))
    mode: str = Field(default="update", pattern="^(update|complete)$")
