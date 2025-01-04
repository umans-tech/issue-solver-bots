from typing import assert_never

from issue_solver.issue_trackers.azure_devops.azure_devops_issue_tracker import (
    AzureDevOpsIssueTracker,
)
from issue_solver.issue_trackers.azure_devops.settings import (
    AzureDevOpsIssueTrackerSettings,
)
from issue_solver.issue_trackers.github.github_issue_tracker import GithubIssueTracker
from issue_solver.issue_trackers.github.settings import GithubIssueTrackerSettings
from issue_solver.issue_trackers.gitlab.gitlab_issue_tracker import GitlabIssueTracker
from issue_solver.issue_trackers.gitlab.settings import GitlabIssueTrackerSettings
from issue_solver.issue_trackers.jira.jira_issue_tracker import JiraIssueTracker
from issue_solver.issue_trackers.jira.settings import JiraIssueTrackerSettings
from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings
from issue_solver.issue_trackers.trello.settings import TrelloIssueTrackerSettings
from issue_solver.issue_trackers.trello.trello_issue_tracker import TrelloIssueTracker
from issue_solver.issue_trackers.url_based.url_based_issue_tracker import (
    UrlBasedIssueTracker,
)

IssueSource = (
    GitlabIssueTracker
    | GithubIssueTracker
    | JiraIssueTracker
    | TrelloIssueTracker
    | AzureDevOpsIssueTracker
    | UrlBasedIssueTracker
)

IssueSourceSettings = (
    GitlabIssueTrackerSettings
    | GithubIssueTrackerSettings
    | JiraIssueTrackerSettings
    | TrelloIssueTrackerSettings
    | AzureDevOpsIssueTrackerSettings
    | ApiBasedIssueTrackerSettings
)


class SupportedIssueTracker:
    @classmethod
    def get(cls, issue_tracker_settings: IssueSourceSettings) -> IssueSource | None:
        match issue_tracker_settings:
            case GitlabIssueTrackerSettings():
                return GitlabIssueTracker.of(
                    settings=issue_tracker_settings,
                )
            case GithubIssueTrackerSettings():
                return GithubIssueTracker()
            case JiraIssueTrackerSettings():
                return JiraIssueTracker()
            case TrelloIssueTrackerSettings():
                return TrelloIssueTracker()
            case AzureDevOpsIssueTrackerSettings():
                return AzureDevOpsIssueTracker()
            case ApiBasedIssueTrackerSettings():
                return UrlBasedIssueTracker()
            case _:
                assert_never(issue_tracker_settings)
