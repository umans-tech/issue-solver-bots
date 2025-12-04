import asyncio
from dataclasses import dataclass
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from issue_solver.clock import UTCSystemClock, Clock
from issue_solver.events.domain import (
    CodeRepositoryIndexed,
    CodeRepositoryIntegrationFailed,
)
from issue_solver.events.event_store import EventStore
from issue_solver.git_operations.git_helper import (
    GitHelper,
    GitValidationError,
    GitSettings,
)
from issue_solver.indexing.repository_indexer import RepositoryIndexer
from issue_solver.indexing.openai_repository_indexer import (
    OpenAIVectorStoreRepositoryIndexer,
)
from issue_solver.factories import init_event_store


class IndexRepositoryCommandSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    repo_url: str
    access_token: str
    knowledge_base_id: str
    webhook_base_url: str
    process_id: str
    repo_path: Path = Field(default=Path("/tmp/repo"))
    from_commit_sha: str | None = Field(default=None)


@dataclass
class IndexRepositoryDependencies:
    event_store: EventStore
    git_helper: GitHelper
    indexer: RepositoryIndexer
    clock: Clock


class IndexRepositoryCommand(IndexRepositoryCommandSettings):
    def cli_cmd(self) -> None:
        asyncio.run(main(self))


async def main(
    settings: IndexRepositoryCommandSettings,
    dependencies: IndexRepositoryDependencies | None = None,
):
    deps = dependencies or await _init_dependencies(settings)

    repo_path = settings.repo_path
    git = deps.git_helper
    clock = deps.clock

    try:
        if settings.from_commit_sha:
            code_version = git.clone_repository(repo_path, depth=None)
            diff = git.get_changed_files_commit(repo_path, settings.from_commit_sha)
            stats = deps.indexer.apply_delta(
                repo_path, diff, settings.knowledge_base_id
            )
        else:
            code_version = git.clone_repository(repo_path, depth=1)
            stats = deps.indexer.upload_full_repository(
                repo_path, settings.knowledge_base_id
            )

        await deps.event_store.append(
            settings.process_id,
            CodeRepositoryIndexed(
                branch=code_version.branch,
                commit_sha=code_version.commit_sha,
                stats=stats,
                knowledge_base_id=settings.knowledge_base_id,
                process_id=settings.process_id,
                occurred_at=clock.now(),
            ),
        )
    except GitValidationError as e:
        await deps.event_store.append(
            settings.process_id,
            CodeRepositoryIntegrationFailed(
                url=settings.repo_url,
                error_type=e.error_type,
                error_message=e.message,
                knowledge_base_id=settings.knowledge_base_id,
                process_id=settings.process_id,
                occurred_at=clock.now(),
            ),
        )
        raise
    except Exception as e:
        await deps.event_store.append(
            settings.process_id,
            CodeRepositoryIntegrationFailed(
                url=settings.repo_url,
                error_type="unexpected_error",
                error_message=str(e),
                knowledge_base_id=settings.knowledge_base_id,
                process_id=settings.process_id,
                occurred_at=clock.now(),
            ),
        )
        raise


async def _init_dependencies(
    settings: IndexRepositoryCommandSettings,
) -> IndexRepositoryDependencies:
    event_store = await init_event_store(webhook_base_url=settings.webhook_base_url)
    git_helper = GitHelper.of(
        git_settings=GitSettings(
            repository_url=settings.repo_url, access_token=settings.access_token
        )
    )
    indexer = OpenAIVectorStoreRepositoryIndexer()
    return IndexRepositoryDependencies(
        event_store=event_store,
        git_helper=git_helper,
        indexer=indexer,
        clock=UTCSystemClock(),
    )
