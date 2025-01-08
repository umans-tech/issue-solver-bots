from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from issue_solver.models.model_settings import ModelSettings
from issue_solver.models.supported_models import SupportedAIModel


class IssueDescription(str):
    pass


@dataclass(frozen=True)
class VersionedAIModel:
    ai_model: SupportedAIModel
    version: str | None = None

    def __repr__(self):
        if self.version:
            return f"{self.ai_model.value}-{self.version}"
        return self.ai_model.value


@dataclass(frozen=True)
class VersionedAIModelWithSettings:
    model: VersionedAIModel
    settings: ModelSettings


@dataclass(frozen=True, kw_only=True)
class ResolveIssueCommand:
    model: VersionedAIModel
    issue_description: IssueDescription
    repo_path: Path


class IssueResolvingAgent(ABC):
    @abstractmethod
    async def resolve_issue(self, command: ResolveIssueCommand) -> None:
        pass
