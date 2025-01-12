from unittest.mock import create_autospec

import docker
import pytest


@pytest.fixture
def stub_docker_client(mocker) -> docker.DockerClient:
    mock_client = create_autospec(docker.DockerClient, instance=True)
    mock_images = create_autospec(docker.models.images.ImageCollection, instance=True)
    mock_containers = create_autospec(
        docker.models.containers.ContainerCollection, instance=True
    )

    mock_client.images = mock_images
    mock_client.containers = mock_containers

    mocker.patch(
        "issue_solver.agents.swe_crafter_on_docker.docker.from_env",
        return_value=mock_client,
    )
    mocker.patch(
        "issue_solver.agents.swe_agent_on_docker.docker.from_env",
        return_value=mock_client,
    )

    yield mock_client
