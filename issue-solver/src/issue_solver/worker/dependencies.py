import uuid
from abc import ABC, abstractmethod
from typing import Callable, Any

from morphcloud.api import MorphCloudClient

from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    DocumentingAgent,
)
from issue_solver.clock import Clock
from issue_solver.events.event_store import EventStore
from issue_solver.git_operations.git_helper import GitClient, GitHelper, GitSettings
from issue_solver.indexing.repository_indexer import RepositoryIndexer
from issue_solver.worker.documenting.knowledge_repository import KnowledgeRepository


class IDGenerator(ABC):
    @abstractmethod
    def new(self) -> str:
        raise NotImplementedError


class UUIDGenerator(IDGenerator):
    def new(self) -> str:
        return str(uuid.uuid4())


class Dependencies:
    def __init__(
        self,
        event_store: EventStore,
        git_client: GitClient,
        coding_agent: IssueResolvingAgent,
        knowledge_repository: KnowledgeRepository,
        clock: Clock,
        microvm_client: MorphCloudClient | None = None,
        is_dev_environment_service_enabled: bool = False,
        id_generator: IDGenerator = UUIDGenerator(),
        docs_agent: DocumentingAgent | None = None,
        git_helper_factory: Callable[[GitSettings, Any | None], GitHelper]
        | None = None,
        repository_indexer: RepositoryIndexer | None = None,
    ):
        self._event_store = event_store
        self.git_client = git_client
        self.coding_agent = coding_agent
        self.knowledge_repository = knowledge_repository
        self.clock = clock
        self.microvm_client = microvm_client
        self.is_dev_environment_service_enabled = is_dev_environment_service_enabled
        self.id_generator = id_generator
        self.docs_agent = docs_agent
        self.git_helper_factory = git_helper_factory
        self.repository_indexer = repository_indexer

    @property
    def event_store(self) -> EventStore:
        return self._event_store
