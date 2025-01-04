from issue_solver.issue_trackers.issue_tracker import IssueTracker, IssueInfo


class AzureDevOpsIssueTracker(IssueTracker):
    def describe_issue(self, issue_id: str) -> IssueInfo | None:
        raise NotImplementedError(
            "AzureDevOpsIssueTracker.get_issue_description is not implemented"
        )
