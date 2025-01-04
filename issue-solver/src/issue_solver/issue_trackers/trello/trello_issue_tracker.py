from issue_solver.issue_trackers.issue_tracker import IssueTracker, IssueInfo


class TrelloIssueTracker(IssueTracker):
    def describe_issue(self, issue_id: str) -> IssueInfo | None:
        raise NotImplementedError(
            "TrelloIssueTracker.get_issue_description is not implemented"
        )
