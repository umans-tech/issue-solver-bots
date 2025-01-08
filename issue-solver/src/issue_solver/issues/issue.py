from dataclasses import dataclass
from pathlib import Path


@dataclass
class IssueInfo:
    description: str
    title: str | None = None


@dataclass
class IssueId:
    id: str


@dataclass
class IssueInternalId:
    project_id: str
    iid: str


IssueReference = IssueId | IssueInternalId | Path
