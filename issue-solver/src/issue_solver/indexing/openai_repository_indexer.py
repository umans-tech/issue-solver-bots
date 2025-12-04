from pathlib import Path
from typing import Callable

from openai import OpenAI

from issue_solver.git_operations.git_helper import GitDiffFiles
from issue_solver.indexing.repository_indexer import RepositoryIndexer
from issue_solver.worker.vector_store_helper import (
    upload_repository_files_to_vector_store,
    get_obsolete_files_ids,
    index_new_files,
    unindex_obsolete_files,
)


class OpenAIVectorStoreRepositoryIndexer(RepositoryIndexer):
    def __init__(
        self,
        client: OpenAI | None = None,
        upload_full: Callable = upload_repository_files_to_vector_store,
        get_obsolete: Callable = get_obsolete_files_ids,
        index_new: Callable = index_new_files,
        unindex: Callable = unindex_obsolete_files,
    ):
        self.client = client or OpenAI()
        self._upload_full = upload_full
        self._get_obsolete = get_obsolete
        self._index_new = index_new
        self._unindex = unindex

    def upload_full_repository(self, repo_path: Path, vector_store_id: str) -> dict:
        return self._upload_full(repo_path, vector_store_id, self.client)

    def apply_delta(
        self, repo_path: Path, diff: GitDiffFiles, vector_store_id: str
    ) -> dict:
        obsolete = self._get_obsolete(
            diff.get_paths_of_all_obsolete_files(), self.client, vector_store_id
        )
        new_files = self._index_new(
            diff.get_paths_of_all_new_files(), self.client, vector_store_id
        )
        unindexed = self._unindex(obsolete.file_ids_path, self.client, vector_store_id)

        return {
            "new_indexed_files": new_files,
            "obsolete_files": obsolete.stats,
            "unindexed_files": unindexed,
        }
