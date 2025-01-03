from issue_solver.issue_trackers.issue_tracker import IssueTracker, IssueInfo


class UrlBasedIssueTracker(IssueTracker):
    def get_issue_description(self, issue_id: str) -> IssueInfo:
        pass
