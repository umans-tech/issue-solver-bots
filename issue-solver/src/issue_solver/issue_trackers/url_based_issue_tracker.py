from issue_solver.issue_trackers.issue_tracker import IssueTracker, IssueInfo


class UrlBasedIssueTracker(IssueTracker):
    def describe_issue(self, issue_id: str) -> IssueInfo | None:
        pass
