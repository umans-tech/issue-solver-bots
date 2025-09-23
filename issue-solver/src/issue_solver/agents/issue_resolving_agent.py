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


class DocumentingAgent(ABC):
    @abstractmethod
    async def generate_documentation(
        self,
        repo_path: Path,
        knowledge_base_id: str,
        output_path: Path,
        docs_prompts: dict[str, str],
        process_id: str,
    ) -> None:
        pass
