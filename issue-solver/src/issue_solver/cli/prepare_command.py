import asyncio
import subprocess
import uuid
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from issue_solver.cli.solve_command_settings import base_settings_to_env_script
from issue_solver.git_operations.git_helper import GitClient
from issue_solver.issues.issue import IssueInfo
from issue_solver.issues.issue_settings import IssueSettings, describe


class PrepareCommandSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    process_id: str
    repo_path: Path
    url: str
    access_token: str | None = None
    issue: IssueInfo | IssueSettings | None = Field(
        description="Reference to the issue "
        "(url, id, iid+project_id or anything that allow the issue tracker to find the issue) "
        "or actual Content describing the issue"
    )
    install_script: Path | str

    def to_env_script(self) -> str:
        return base_settings_to_env_script(self)


class PrepareCommand(PrepareCommandSettings):
    def cli_cmd(self) -> None:
        asyncio.run(self.run_prepare())

    async def run_prepare(self) -> None:
        return await main(self)


async def main(settings: PrepareCommandSettings) -> None:
    issue_info = describe(settings.issue) if settings.issue else None
    process_id = settings.process_id or str(uuid.uuid4())
    print(
        f"[prepare] 🏗️ Preparing workspace for resolving issue='{settings.issue}' in repo={settings.repo_path} with process_id={settings.process_id}"
    )
    GitClient.clone_repo_and_branch(
        repo_path=settings.repo_path,
        url=settings.url,
        access_token=settings.access_token,
        process_id=process_id,
        issue=issue_info,
    )
    command = (
        settings.install_script
        if not Path(settings.install_script).is_file()
        else Path(settings.install_script).read_text()
    )
    print(f"[prepare] 🏗️ Running install script: in repo={settings.repo_path}")
    subprocess.run(command, shell=True, check=True, cwd=settings.repo_path)
