from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from issue_solver.issues.issue import IssueInfo
from issue_solver.models.model_settings import ModelSettings
from issue_solver.models.supported_models import VersionedAIModel


@dataclass(frozen=True)
class VersionedAIModelWithSettings:
    model: VersionedAIModel
    settings: ModelSettings


@dataclass(frozen=True, kw_only=True)
class ResolveIssueCommand:
    model: VersionedAIModel
    issue: IssueInfo
    repo_path: Path
    process_id: str


class IssueResolvingAgent(ABC):
    @abstractmethod
    async def resolve_issue(self, command: ResolveIssueCommand) -> None:
        pass
