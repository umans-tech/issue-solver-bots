from typing import assert_never

from issue_solver.issues.trackers.azure_devops_issue_tracker import (
    AzureDevOpsIssueTracker,
)
from issue_solver.issues.trackers.github_issue_tracker import GithubIssueTracker
from issue_solver.issues.trackers.gitlab_issue_tracker import GitlabIssueTracker
from issue_solver.issues.trackers.http_based_issue_tracker import HttpBasedIssueTracker
from issue_solver.issues.trackers.jira_issue_tracker import JiraIssueTracker
from issue_solver.issues.trackers.notion_issue_tracker import NotionIssueTracker
from issue_solver.issues.trackers.trello_issue_tracker import TrelloIssueTracker

IssueSource = (
    GitlabIssueTracker
    | GithubIssueTracker
    | JiraIssueTracker
    | TrelloIssueTracker
    | AzureDevOpsIssueTracker
    | HttpBasedIssueTracker
    | NotionIssueTracker
)

IssueSourceSettings = (
    GitlabIssueTracker.Settings
    | GithubIssueTracker.Settings
    | JiraIssueTracker.Settings
    | TrelloIssueTracker.Settings
    | AzureDevOpsIssueTracker.Settings
    | HttpBasedIssueTracker.Settings
    | NotionIssueTracker.Settings
)


class SupportedIssueTracker:
    @classmethod
    def get(cls, issue_tracker_settings: IssueSourceSettings) -> IssueSource:
        match issue_tracker_settings:
            case GitlabIssueTracker.Settings():
                return GitlabIssueTracker.of(
                    settings=issue_tracker_settings,
                )
            case GithubIssueTracker.Settings():
                return GithubIssueTracker(settings=issue_tracker_settings)
            case JiraIssueTracker.Settings():
                return JiraIssueTracker()
            case TrelloIssueTracker.Settings():
                return TrelloIssueTracker.of(settings=issue_tracker_settings)
            case AzureDevOpsIssueTracker.Settings():
                return AzureDevOpsIssueTracker()
            case HttpBasedIssueTracker.Settings():
                return HttpBasedIssueTracker()
            case NotionIssueTracker.Settings():
                return NotionIssueTracker.of(settings=issue_tracker_settings)
            case _:
                assert_never(issue_tracker_settings)
