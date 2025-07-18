from unittest.mock import create_autospec

import docker
import pytest
from docker.models.containers import ContainerCollection, Container
from docker.models.images import ImageCollection

from issue_solver.agents.issue_resolving_agent import (
    ResolveIssueCommand,
)
from issue_solver.agents.swe_agents_on_docker import (
    SweAgentOnDocker,
    SweCrafterOnDocker,
)
from issue_solver.issues.issue import IssueInfo
from issue_solver.models.model_settings import OpenAISettings
from issue_solver.models.supported_models import SupportedOpenAIModel, VersionedAIModel


@pytest.fixture
def stub_docker_client(monkeypatch) -> docker.DockerClient:
    """
    A pytest fixture that stubs out docker.from_env() so we do NOT run real containers.
    Returns a mocked DockerClient with mocked images and containers.
    """
    mock_client = create_autospec(docker.DockerClient, instance=True)
    mock_images = create_autospec(ImageCollection, instance=True)
    mock_containers = create_autospec(ContainerCollection, instance=True)

    mock_client.images = mock_images
    mock_client.containers = mock_containers

    def mock_from_env():
        return mock_client

    # Replace docker.from_env with our local function
    monkeypatch.setattr(docker, "from_env", mock_from_env)

    return mock_client


@pytest.fixture
def sample_issue() -> IssueInfo:
    """
    A minimal IssueInfo object for testing.
    """
    return IssueInfo(title="Test Issue", description="This is a stub-based test.")


@pytest.fixture
def sample_command(tmp_path, sample_issue) -> ResolveIssueCommand:
    """
    A ResolveIssueCommand that might come from your Pydantic AppSettings or
    be built directly in the test. For simplicity, we hardcode here.
    """
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    return ResolveIssueCommand(
        model=VersionedAIModel(SupportedOpenAIModel.GPT4O),
        issue=sample_issue,
        repo_path=repo_dir,
        process_id="test-process-id-12345",
    )


@pytest.mark.asyncio
async def test_swe_crafter_on_docker_success(stub_docker_client, sample_command):
    """
    Test that SweCrafterOnDocker properly pulls images, runs a container,
    and completes successfully (exit code 0).
    """
    # Arrange
    # Stub for container
    mock_container = create_autospec(Container, instance=True)
    mock_container.logs.return_value = [b"Stub container log line\n"]
    mock_container.wait.return_value = {"StatusCode": 0}

    # Make .run() return our container stub
    stub_docker_client.containers.run.return_value = mock_container

    open_ai_settings = OpenAISettings(api_key="s3cr3t-k3y")
    agent = SweCrafterOnDocker(open_ai_settings)

    # Act (should not raise exception if exit code is 0)
    await agent.resolve_issue(sample_command)

    # Assert - images pulled
    stub_docker_client.images.pull.assert_any_call("umans/swe-crafter-run")
    stub_docker_client.images.pull.assert_any_call("umans/swe-crafter")

    # Assert - container was run with expected arguments
    assert stub_docker_client.containers.run.call_count == 1
    _, kwargs = stub_docker_client.containers.run.call_args
    assert "/var/run/docker.sock" in kwargs["volumes"]
    assert str(sample_command.repo_path) in kwargs["volumes"]
    assert kwargs["image"] == "umans/swe-crafter-run"
    # Check environment or command as needed
    cmd = kwargs["command"]
    assert "--model_name" in cmd
    assert "--repo_path" in cmd
    tmp_file_path = sample_command.repo_path / "issue_info.md"
    assert not tmp_file_path.exists(), "Temporary file issue_info.md should be deleted."


@pytest.mark.asyncio
async def test_swe_crafter_on_docker_non_zero_exit(stub_docker_client, sample_command):
    """
    Test that SweCrafterOnDocker raises RuntimeError if container exits with non-zero code.
    """
    # Arrange
    mock_container = create_autospec(Container, instance=True)
    mock_container.logs.return_value = [b"Simulated error"]
    mock_container.wait.return_value = {"StatusCode": 42}
    stub_docker_client.containers.run.return_value = mock_container

    open_ai_settings = OpenAISettings(api_key="s3cr3t-k3y")
    agent = SweCrafterOnDocker(open_ai_settings)

    # Act & Assert
    with pytest.raises(RuntimeError, match="exited with code 42"):
        await agent.resolve_issue(sample_command)


@pytest.mark.asyncio
async def test_swe_agent_on_docker_success(stub_docker_client, sample_command):
    """
    Test that SweAgentOnDocker properly pulls images, runs a container,
    and completes successfully (exit code 0).
    """
    # Arrange
    mock_container = create_autospec(Container, instance=True)
    mock_container.logs.return_value = [b"SweAgentOnDocker success log\n"]
    mock_container.wait.return_value = {"StatusCode": 0}
    stub_docker_client.containers.run.return_value = mock_container

    open_ai_settings = OpenAISettings(api_key="s3cr3t-k3y")
    agent = SweAgentOnDocker(open_ai_settings)

    # Act
    await agent.resolve_issue(sample_command)

    # Assert
    stub_docker_client.images.pull.assert_any_call("sweagent/swe-agent-run:latest")
    stub_docker_client.images.pull.assert_any_call("sweagent/swe-agent:latest")
    assert stub_docker_client.containers.run.call_count == 1
    _, kwargs = stub_docker_client.containers.run.call_args
    assert kwargs["image"] == "sweagent/swe-agent-run:latest"
    assert str(sample_command.repo_path) in kwargs["volumes"]


@pytest.mark.asyncio
async def test_swe_agent_on_docker_non_zero_exit(stub_docker_client, sample_command):
    """
    Test that SweAgentOnDocker raises RuntimeError if container exits with non-zero code.
    """
    # Arrange
    mock_container = create_autospec(Container, instance=True)
    mock_container.logs.return_value = [b"Simulated agent error"]
    mock_container.wait.return_value = {"StatusCode": 99}
    stub_docker_client.containers.run.return_value = mock_container

    open_ai_settings = OpenAISettings(api_key="s3cr3t-k3y")
    agent = SweAgentOnDocker(open_ai_settings)

    # Act & Assert
    with pytest.raises(RuntimeError, match="exited with code 99"):
        await agent.resolve_issue(sample_command)
