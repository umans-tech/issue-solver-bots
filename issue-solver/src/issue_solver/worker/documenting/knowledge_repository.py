from abc import abstractmethod, ABC
from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeBase:
    id: str
    version: str


class KnowledgeRepository(ABC):
    @abstractmethod
    def contains(self, base: KnowledgeBase, document_name: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def add(self, base: KnowledgeBase, document_name: str, content: str) -> None:
        pass

    @abstractmethod
    def list_entries(self, base: KnowledgeBase) -> list[str]:
        pass

    @abstractmethod
    def get_content(self, base: KnowledgeBase, document_name: str) -> str:
        pass
