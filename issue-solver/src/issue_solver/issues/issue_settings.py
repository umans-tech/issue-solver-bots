from dataclasses import dataclass
from typing import assert_never

from issue_solver.issues.issue import IssueReference, IssueInfo
from issue_solver.issues.trackers.supported_issue_trackers import (
    IssueSourceSettings,
    SupportedIssueTracker,
)


@dataclass
class IssueSettings:
    tracker: IssueSourceSettings
    ref: IssueReference


def describe(issue: IssueInfo | IssueSettings) -> IssueInfo:
    issue_info = None
    match issue:
        case IssueSettings():
            issue_tracker = SupportedIssueTracker.get(issue.tracker)
            issue_info = issue_tracker.describe_issue(issue.ref)
        case IssueInfo():
            issue_info = issue
        case _:
            assert_never(issue)
    if issue_info is None:
        raise ValueError("Issue info could not be found. for issue: {issue}")
    return issue_info
