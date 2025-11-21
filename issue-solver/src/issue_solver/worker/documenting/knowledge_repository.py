from abc import abstractmethod, ABC
from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeBase:
    id: str
    version: str


@dataclass(frozen=True)
class DocRef:
    base: KnowledgeBase
    document_name: str


class KnowledgeRepository(ABC):
    @abstractmethod
    def contains(self, base: KnowledgeBase, document_name: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def add(
        self,
        base: KnowledgeBase,
        document_name: str,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    def list_entries(self, base: KnowledgeBase) -> list[str]:
        pass

    @abstractmethod
    def get_content(self, base: KnowledgeBase, document_name: str) -> str:
        pass

    @abstractmethod
    def get_metadata(self, base: KnowledgeBase, document_name: str) -> dict[str, str]:
        pass

    def get_origin(self, base: KnowledgeBase, document_name: str) -> str | None:
        return self.get_metadata(base, document_name).get("origin")
