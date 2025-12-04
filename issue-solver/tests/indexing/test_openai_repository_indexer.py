from pathlib import Path
from threading import Lock
from types import SimpleNamespace

import pytest

from typing import Any

from issue_solver.git_operations.git_helper import GitDiffFiles
from issue_solver.indexing.openai_repository_indexer import (
    OpenAIVectorStoreRepositoryIndexer,
)


def test_upload_full_repository_links_files(client: Any, repo: Path):
    # Given
    indexer = OpenAIVectorStoreRepositoryIndexer(client=client)

    # When
    stats = indexer.upload_full_repository(repo, "kb-123")

    # Then
    assert stats["successful_uploads"] == 3  # three files in repo
    linked_paths = {
        attrs["file_path"] for _, _, attrs in client.vector_stores.files.links
    }
    assert linked_paths == {"/src/keep.py", "/src/old.py", "/src/new.py"}


def test_apply_delta_indexes_new_and_unindexes_obsolete(client: Any, repo: Path):
    # Given
    # Seed vector store with an existing file mapping for old.py
    # Simulate previous index: create and link old.py
    old_file_resp = client.files.create(
        file=open(repo / "src" / "old.py", "rb"), purpose="assistants"
    )
    client.vector_stores.files.create(
        vector_store_id="kb-123",
        file_id=old_file_resp.id,
        attributes={"file_path": "/src/old.py"},
    )

    diff = GitDiffFiles(
        repo_path=repo,
        added_files=[Path("src/new.py")],
        deleted_files=[Path("src/old.py")],
        modified_files=[Path("src/keep.py")],
        renamed_files=[],
    )

    indexer = OpenAIVectorStoreRepositoryIndexer(client=client)

    # When
    stats = indexer.apply_delta(repo, diff, "kb-123")

    # Then
    # New and modified files get indexed
    assert stats["new_indexed_files"]["successful_uploads"] == 2
    # Obsolete search captured one file
    assert stats["obsolete_files"]["successful_search"] == 1
    # Unindexed obsolete file
    assert stats["unindexed_files"]["successful_unindexing"] == 1

    # Links should now include keep.py and new.py, but not old.py
    linked_paths = {
        attrs["file_path"] for _, _, attrs in client.vector_stores.files.links
    }
    assert linked_paths == {"/src/keep.py", "/src/new.py"}


@pytest.fixture
def client() -> Any:
    return FakeOpenAIClient()


@pytest.fixture
def repo() -> Path:
    repo_path = Path("/tmp/repo/test-indexer")
    if repo_path.exists():
        for child in repo_path.rglob("*"):
            if child.is_file():
                child.unlink()
        for child in sorted(repo_path.rglob("*"), reverse=True):
            if child.is_dir():
                child.rmdir()
    (repo_path / "src").mkdir(parents=True, exist_ok=True)
    (repo_path / "src" / "keep.py").write_text("print('keep')\n")
    (repo_path / "src" / "old.py").write_text("print('old')\n")
    (repo_path / "src" / "new.py").write_text("print('new')\n")
    return repo_path


class FakeFilesAPI:
    def __init__(self):
        self._next_id = 1
        self._store: dict[str, bytes] = {}
        self._lock = Lock()

    def create(self, file, purpose: str):  # noqa: A003 - API parity
        content = file.read()
        with self._lock:
            file_id = f"file-{self._next_id}"
            self._next_id += 1
            self._store[file_id] = content
        return SimpleNamespace(id=file_id)


class FakeVectorStoreFilesAPI:
    def __init__(self, parent):
        self.parent = parent
        self.links: list[tuple[str, str, dict]] = []
        self._lock = Lock()

    def create(self, vector_store_id: str, file_id: str, attributes: dict):
        with self._lock:
            self.links.append((vector_store_id, file_id, attributes))
        return SimpleNamespace(id=file_id)

    def delete(self, vector_store_id: str, file_id: str):
        with self._lock:
            self.links = [link for link in self.links if link[1] != file_id]
        return SimpleNamespace(id=file_id, deleted=True)


class FakeVectorStoresAPI:
    def __init__(self, parent):
        self.parent = parent
        self.files = FakeVectorStoreFilesAPI(parent)

    def search(self, vector_store_id: str, query: str, filters, max_num_results: int):
        matches = [
            SimpleNamespace(file_id=file_id)
            for vs_id, file_id, attrs in self.files.links
            if vs_id == vector_store_id and attrs.get("file_path") == query
        ]
        return SimpleNamespace(data=matches)


class FakeOpenAIClient:
    def __init__(self):
        self.files = FakeFilesAPI()
        self.vector_stores = FakeVectorStoresAPI(self)
