import tempfile

from issue_solver.worker.vector_store_helper import (
    path_from_repo_root,
    prepare_file_path_to_upload,
)


def test_path_from_repo_root():
    # Given
    file_path = "/tmp/repo/0329720391473209742390/docs/adr/2024-02-13-feature-flipping-naming-and-usage.md"

    # When
    result = path_from_repo_root(file_path)

    # Then
    assert result == "/docs/adr/2024-02-13-feature-flipping-naming-and-usage.md"


def test_prepare_file_path_to_upload_with_unsupported_extension():
    # Given
    file_name = "place-order.feature"

    with tempfile.NamedTemporaryFile(
        suffix=file_name
    ) as file_with_unsupported_extension:
        # When
        result = prepare_file_path_to_upload(file_with_unsupported_extension.name)

        # Then
        assert result == file_with_unsupported_extension.name + ".txt"


def test_prepare_file_path_to_upload_with_supported_extension():
    # Given
    file_name = "place-order.py"

    with tempfile.NamedTemporaryFile(suffix=file_name) as file_with_supported_extension:
        # When
        result = prepare_file_path_to_upload(file_with_supported_extension.name)

        # Then
        assert result == file_with_supported_extension.name


def test_prepare_file_path_to_upload_with_dockerfile():
    # Given
    with tempfile.NamedTemporaryFile(suffix="Dockerfile", delete=False) as dockerfile:
        # When
        result = prepare_file_path_to_upload(dockerfile.name)

        # Then
        assert result == dockerfile.name


def test_prepare_file_path_to_upload_with_dockerfile_lowercase():
    # Given
    with tempfile.NamedTemporaryFile(suffix="dockerfile", delete=False) as dockerfile:
        # When
        result = prepare_file_path_to_upload(dockerfile.name)

        # Then
        assert result == dockerfile.name


def test_prepare_file_path_to_upload_with_dockerfile_extension():
    # Given
    file_name = "webapi.dockerfile"

    with tempfile.NamedTemporaryFile(suffix=file_name) as dockerfile_with_extension:
        # When
        result = prepare_file_path_to_upload(dockerfile_with_extension.name)

        # Then
        assert result == dockerfile_with_extension.name


def test_prepare_file_path_to_upload_with_terraform_file():
    # Given
    file_name = "main.tf"

    with tempfile.NamedTemporaryFile(suffix=file_name) as terraform_file:
        # When
        result = prepare_file_path_to_upload(terraform_file.name)

        # Then
        assert result == terraform_file.name


def test_prepare_file_path_to_upload_with_dockerfile_uppercase_extension():
    # Given
    file_name = "worker.Dockerfile"

    with tempfile.NamedTemporaryFile(suffix=file_name) as dockerfile_with_extension:
        # When
        result = prepare_file_path_to_upload(dockerfile_with_extension.name)

        # Then
        assert result == dockerfile_with_extension.name
