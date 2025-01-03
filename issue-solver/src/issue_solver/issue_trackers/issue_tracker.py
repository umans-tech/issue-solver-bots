from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IssueInfo:
    title: str
    description: str


class IssueTracker(ABC):
    @abstractmethod
    def get_issue_description(self, issue_id: str) -> IssueInfo:
        pass
