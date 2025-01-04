from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IssueInfo:
    title: str
    description: str


class IssueTracker(ABC):
    @abstractmethod
    def describe_issue(self, issue_id: str) -> IssueInfo | None:
        pass
