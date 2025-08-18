import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from issue_solver.git_operations.git_helper import (
    GitHelper,
    GitSettings,
    extract_git_clone_default_directory_name,
)


@pytest.fixture
def mock_repo():
    """Create a mocked git repository for testing."""
    repo = Mock()
    repo.git.diff.return_value = (
        "A\tnew_file.txt\nM\tfile1.txt\nD\tfile2.txt\nR100\told_name.txt\tnew_name.txt"
    )
    return repo


@patch("issue_solver.git_operations.git_helper.Repo")
def test_get_changed_files_commit(mock_repo_class, mock_repo):
    """Test that get_changed_files_commit correctly parses git diff output."""
    # Given
    mock_repo_class.return_value = mock_repo
    repo_path = Path("/mock/repo/path")
    commit_sha = "abcd1234"
    git_helper = GitHelper(GitSettings(access_token="dummy_token"))

    # When
    diff_files = git_helper.get_changed_files_commit(repo_path, commit_sha)

    # Then
    mock_repo_class.assert_called_once_with(repo_path)
    mock_repo.git.diff.assert_called_once_with("--name-status", commit_sha, "HEAD")

    assert diff_files.repo_path == repo_path
    assert Path("new_file.txt") in diff_files.added_files
    assert Path("file1.txt") in diff_files.modified_files
    assert Path("file2.txt") in diff_files.deleted_files

    assert len(diff_files.renamed_files) == 1
    renamed_file = diff_files.renamed_files[0]
    assert renamed_file.old_file_name == Path("old_name.txt")
    assert renamed_file.new_file_name == Path("new_name.txt")


@pytest.mark.parametrize(
    "repo_url,expected_directory",
    [
        # GitHub HTTPS URLs
        ("https://github.com/user/my-project.git", "my-project"),
        ("https://github.com/user/awesome-app", "awesome-app"),
        ("https://github.com/facebook/react.git", "react"),
        # SSH URLs
        ("git@github.com:user/repo-name.git", "repo-name"),
        ("git@gitlab.com:group/project.git", "project"),
        # Local paths
        ("/path/to/local/repo.git", "repo"),
        ("/home/user/projects/my-app.git", "my-app"),
        # Other formats
        ("host.xz:foo/.git", "foo"),
        ("https://gitlab.com/group/subgroup/project.git", "project"),
        # Trailing slashes
        ("https://github.com/user/project/", "project"),
        ("https://github.com/user/my-repo.git/", "my-repo"),
        # Edge cases
        ("simple-repo.git", "simple-repo"),
        ("simple-repo", "simple-repo"),
    ],
)
def test_git_clone_directory_name(repo_url, expected_directory):
    # Test the problematic case
    assert extract_git_clone_default_directory_name(repo_url) == expected_directory
