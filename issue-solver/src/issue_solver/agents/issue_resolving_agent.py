from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from issue_solver.models.supported_models import SupportedAIModel


class IssueDescription(str):
    pass


@dataclass(frozen=True, kw_only=True)
class ResolveIssueCommand:
    model: SupportedAIModel
    issue_description: IssueDescription
    repo_path: Path


class IssueResolvingAgent(ABC):
    @abstractmethod
    async def resolve_issue(self, command: ResolveIssueCommand) -> None:
        pass
