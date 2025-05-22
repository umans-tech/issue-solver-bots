from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import docker
from pydantic_settings import BaseSettings

from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    ResolveIssueCommand,
)
from issue_solver.models.model_settings import ModelSettings


class SweAgentOnDocker(IssueResolvingAgent):
    AGENT_IMAGE = "sweagent/swe-agent:latest"
    AGENT_RUNNER_IMAGE = "sweagent/swe-agent-run:latest"
    CONFIG_FILE = "config/default_from_url.yaml"

    def __init__(self, *ai_models_settings: ModelSettings):
        super().__init__()
        self.env_vars: dict[str, Any] = {}
        for ai_model_settings in ai_models_settings:
            settings_model_dump = to_dict_with_prefix(ai_model_settings)
            self.env_vars.update(settings_model_dump)

    async def resolve_issue(self, command: ResolveIssueCommand) -> None:
        """
        Pull and run the 'sweagent/swe-agent-run:latest' Docker image to resolve the issue,
        passing volumes/environment variables as in solve_issues.sh.
        """
        env_vars = self.env_vars
        repo_path = Path(command.repo_path).resolve()
        print(f"Resolving issue in {repo_path}")
        repo_name = repo_path.name
        repo_path_inside_container = f"/app/repo/{repo_name}"

        tmp_file_path = repo_path / "issue_info.md"
        tmp_file_path.write_text(
            f"# {command.issue.title}\n\n{command.issue.description}"
        )
        data_file_in_container = f"{repo_path_inside_container}/issue_info.md"

        container_command = [
            "python",
            "run.py",
            "--image_name",
            self.AGENT_IMAGE,
            "--model_name",
            str(command.model),
            "--data_path",
            data_file_in_container,
            "--repo_path",
            repo_path_inside_container,
            "--apply_patch_locally",
            "--config_file",
            self.CONFIG_FILE,
            "--skip_existing=False",
        ]

        volumes = {
            "/var/run/docker.sock": {
                "bind": "/var/run/docker.sock",
                "mode": "rw",
            },
            str(repo_path): {
                "bind": repo_path_inside_container,
                "mode": "rw",
            },
        }

        with docker_client_context() as client:
            client.images.pull(self.AGENT_RUNNER_IMAGE)
            client.images.pull(self.AGENT_IMAGE)

            container = client.containers.run(
                image=self.AGENT_RUNNER_IMAGE,
                command=container_command,
                environment=env_vars,
                volumes=volumes,
                detach=True,
                tty=True,
                remove=True,
            )

            for log_line in container.logs(stream=True):
                print(log_line.decode("utf-8", errors="replace"), end="")

            result = container.wait()
            exit_code = result.get("StatusCode", 1)
            if exit_code != 0:
                raise RuntimeError(
                    f"SweAgentOnDocker container exited with code {exit_code}"
                )

        tmp_file_path.unlink(missing_ok=True)


class SweCrafterOnDocker(SweAgentOnDocker):
    AGENT_IMAGE = "umans/swe-crafter"
    AGENT_RUNNER_IMAGE = "umans/swe-crafter-run"
    CONFIG_FILE = "config/test-first_from_url.yaml"


@contextmanager
def docker_client_context() -> Generator[docker.DockerClient, None, None]:
    """
    Yields a Docker client, ensuring it gets closed automatically.
    """
    client = docker.from_env()
    try:
        yield client
    finally:
        client.close()


def to_dict_with_prefix(ai_model_settings: BaseSettings) -> dict[str, Any]:
    settings_model_dump = ai_model_settings.model_dump(by_alias=True)
    if ai_model_settings.model_config.get("env_prefix"):
        settings_model_dump = {
            f"{ai_model_settings.model_config.get('env_prefix')}{k}".upper(): v
            for k, v in settings_model_dump.items()
        }
    return settings_model_dump
