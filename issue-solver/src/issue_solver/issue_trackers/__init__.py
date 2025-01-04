from enum import StrEnum

from issue_solver.issue_trackers.azure_devops_issue_tracker import (
    AzureDevOpsIssueTracker,
)
from issue_solver.issue_trackers.github_issue_tracker import GithubIssueTracker
from issue_solver.issue_trackers.github_pull_request import GithubPullRequest
from issue_solver.issue_trackers.gitlab_issue_tracker import GitlabIssueTracker
from issue_solver.issue_trackers.gitlab_merge_request import GitlabMergeRequest
from issue_solver.issue_trackers.jira_issue_tracker import JiraIssueTracker
from issue_solver.issue_trackers.trello_issue_tracker import TrelloIssueTracker
from issue_solver.issue_trackers.url_based_issue_tracker import UrlBasedIssueTracker

IssueSource = (
    GitlabIssueTracker
    | GitlabMergeRequest
    | GithubIssueTracker
    | GithubPullRequest
    | JiraIssueTracker
    | TrelloIssueTracker
    | AzureDevOpsIssueTracker
    | UrlBasedIssueTracker
)


class SupportedIssueTracker(StrEnum):
    GITLAB = "gitlab"
    GITLAB_MR = "gitlab_mr"
    GITHUB = "github"
    GITHUB_PR = "github_pr"
    JIRA = "jira"
    TRELLO = "trello"
    AZURE_DEVOPS = "azure_devops"
    URL_BASED = "url_based"

    @classmethod
    def get(cls, issue_tracker: str) -> IssueSource | None:
        match issue_tracker:
            case cls.GITLAB:
                return GitlabIssueTracker.of(
                    base_url="https://gitlab.com",
                    private_token="dummy-token",
                    api_version="4",
                    project_id="58400527",
                )
            case cls.GITHUB:
                return GithubIssueTracker()
            case cls.JIRA:
                return JiraIssueTracker()
            case cls.TRELLO:
                return TrelloIssueTracker()
            case cls.AZURE_DEVOPS:
                return AzureDevOpsIssueTracker()
            case cls.GITLAB_MR:
                return GitlabMergeRequest()
            case cls.GITHUB_PR:
                return GithubPullRequest()
            case cls.URL_BASED:
                return UrlBasedIssueTracker()
            case _:
                return None
