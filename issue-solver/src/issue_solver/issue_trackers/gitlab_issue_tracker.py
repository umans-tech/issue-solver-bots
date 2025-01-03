from issue_solver.issue_trackers.issue_tracker import IssueTracker, IssueInfo


class GitlabIssueTracker(IssueTracker):
    def get_issue_description(self, issue_id: str) -> IssueInfo:
        raise NotImplementedError(
            "GitlabIssueTracker.get_issue_description is not implemented"
        )
