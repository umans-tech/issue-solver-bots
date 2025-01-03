from issue_solver.issue_trackers.issue_tracker import IssueTracker, IssueInfo


class JiraIssueTracker(IssueTracker):
    def get_issue_description(self, issue_id: str) -> IssueInfo:
        raise NotImplementedError(
            "JiraIssueTracker.get_issue_description is not implemented"
        )
