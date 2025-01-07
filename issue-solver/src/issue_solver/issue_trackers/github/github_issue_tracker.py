from issue_solver.issue_trackers.issue_tracker import (
    IssueTracker,
    IssueInfo,
    IssueReference,
)


class GithubIssueTracker(IssueTracker):
    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        raise NotImplementedError(
            "GithubIssueTracker.get_issue_description is not implemented"
        )
