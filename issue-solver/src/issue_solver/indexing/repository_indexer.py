from abc import ABC, abstractmethod
from pathlib import Path

from issue_solver.git_operations.git_helper import GitDiffFiles


class RepositoryIndexer(ABC):
    @abstractmethod
    def upload_full_repository(self, repo_path: Path, vector_store_id: str) -> dict:
        """Upload the full repository to the vector store and return stats."""

    @abstractmethod
    def apply_delta(
        self, repo_path: Path, diff: GitDiffFiles, vector_store_id: str
    ) -> dict:
        """Apply a delta (new/changed + obsolete removals) and return stats."""
