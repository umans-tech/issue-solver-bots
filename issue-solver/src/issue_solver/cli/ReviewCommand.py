from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReviewSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    repo_path: Path = Field(default=Path("."))

    def cli_cmd(self) -> None:
        print(f"[review] 👀 Reviewing in repo={self.repo_path}")
