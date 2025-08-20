from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelSettings(BaseSettings):
    api_key: str = Field(description="API key for the model.")
    base_url: AnyUrl | None = Field(description="Base URL for the model.")


class OpenAISettings(ModelSettings):
    base_url: AnyUrl | None = Field(
        description="Base URL for the model.",
        default=AnyUrl("https://api.openai.com/v1"),
    )

    model_config = SettingsConfigDict(
        env_prefix="OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DeepSeekSettings(ModelSettings):
    base_url: AnyUrl | None = Field(
        description="Base URL for the model.",
        default=AnyUrl("https://api.deepseek.com/v1"),
    )

    model_config = SettingsConfigDict(
        env_prefix="DEEPSEEK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AnthropicSettings(ModelSettings):
    base_url: AnyUrl | None = Field(
        description="Base URL for the model.",
        default=AnyUrl("https://api.anthropic.com"),
    )

    model_config = SettingsConfigDict(
        env_prefix="ANTHROPIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class QwenSettings(ModelSettings):
    base_url: AnyUrl | None = Field(
        description="Base URL for the model.",
        default=AnyUrl("https://api.aimlapi.com/v1"),
    )

    model_config = SettingsConfigDict(
        env_prefix="QWEN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
