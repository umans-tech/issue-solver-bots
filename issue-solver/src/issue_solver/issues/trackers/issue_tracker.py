from abc import ABC, abstractmethod

from issue_solver.issues.issue import IssueReference, IssueInfo


class IssueTracker(ABC):
    @abstractmethod
    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        pass
