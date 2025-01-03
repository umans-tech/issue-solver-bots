from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings

from issue_solver.models.supported_models import SupportedLLMModel


class ModelSettings(BaseSettings):
    model_name: SupportedLLMModel = Field(
        description="Which model to use for the agent."
    )
    api_key: str = Field(description="API key for the model.")
    base_url: AnyUrl | None = Field(description="Base URL for the model.")


class OpenAISettings(ModelSettings):
    pass

    class Config:
        env_prefix = "OPENAI_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class DeepSeekSettings(ModelSettings):
    pass

    class Config:
        env_prefix = "DEEPSEEK_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class AnthropicSettings(ModelSettings):
    pass

    class Config:
        env_prefix = "ANTHROPIC_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class QwenSettings(ModelSettings):
    pass

    class Config:
        env_prefix = "QWEN_"
        env_file = ".env"
        env_file_encoding = "utf-8"
