from issue_solver.issue_trackers.issue_tracker import IssueTracker, IssueInfo


class GitlabMergeRequest(IssueTracker):
    def describe_issue(self, issue_id: str) -> IssueInfo | None:
        raise NotImplementedError(
            "GitlabMergeRequest.get_issue_description is not implemented"
        )
