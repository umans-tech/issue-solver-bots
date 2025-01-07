from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IssueInfo:
    description: str
    title: str | None = None


class IssueTracker(ABC):
    @abstractmethod
    def describe_issue(self, issue_id: str) -> IssueInfo | None:
        pass
