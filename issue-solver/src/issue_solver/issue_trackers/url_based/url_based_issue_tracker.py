from issue_solver.issue_trackers.issue_tracker import (
    IssueTracker,
    IssueInfo,
    IssueReference,
)


class UrlBasedIssueTracker(IssueTracker):
    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        pass
