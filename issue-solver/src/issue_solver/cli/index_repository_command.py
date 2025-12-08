import asyncio
import uuid
from dataclasses import dataclass
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from issue_solver.clock import UTCSystemClock, Clock
from issue_solver.cli.solve_command_settings import base_settings_to_env_script
from issue_solver.events.domain import (
    CodeRepositoryIndexed,
    CodeRepositoryIntegrationFailed,
    most_recent_event,
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
    access_token: str | None = Field(
        default=None, description="Access token if the repository is private"
    )
    knowledge_base_id: str
    webhook_base_url: str | None = Field(
        default=None,
        description="Webhook base URL to send events and or messages related to issue resolution process. If not provided, no webhook will be used.",
    )
    database_url: str | None = Field(
        default=None,
        description="Database URL for storing events. If not provided, an in-memory store is used.",
    )
    process_queue_url: str | None = Field(
        default=None,
        description="SQS Queue URL for event streaming. Mutually exclusive with webhook_base_url.",
    )
    process_id: str | None = Field(
        default=None,
        description="Process ID for the indexing. If not provided, a UUID will be generated.",
    )
    repo_path: Path = Field(default=Path("/tmp/repo"))
    from_commit_sha: str | None = Field(default=None)

    def to_env_script(self) -> str:
        return base_settings_to_env_script(self)


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
) -> str:
    deps = dependencies or await _init_dependencies(settings)

    repo_path = settings.repo_path
    git = deps.git_helper
    clock = deps.clock
    from_commit_sha = await _resolve_from_commit_sha(deps.event_store, settings)
    process_id = settings.process_id or str(uuid.uuid4())

    try:
        if from_commit_sha:
            print(
                (
                    "[index-repository] starting delta mode "
                    f"from={from_commit_sha} "
                    f"repo={settings.repo_url} "
                    f"kb={settings.knowledge_base_id}"
                )
            )
            code_version = git.clone_repository(repo_path, depth=None)
            diff = git.get_changed_files_commit(repo_path, from_commit_sha)
            stats = deps.indexer.apply_delta(
                repo_path, diff, settings.knowledge_base_id
            )
            print(
                (
                    "[index-repository] delta mode "
                    f"from={from_commit_sha} "
                    f"new_files={len(diff.get_paths_of_all_new_files())} "
                    f"obsolete_files={len(diff.get_paths_of_all_obsolete_files())} "
                    f"branch={code_version.branch} commit={code_version.commit_sha}"
                )
            )
        else:
            print(
                (
                    "[index-repository] starting full mode "
                    f"repo={settings.repo_url} "
                    f"kb={settings.knowledge_base_id}"
                )
            )
            code_version = git.clone_repository(repo_path, depth=1)
            stats = deps.indexer.upload_full_repository(
                repo_path, settings.knowledge_base_id
            )
            print(
                (
                    "[index-repository] full mode "
                    f"branch={code_version.branch} commit={code_version.commit_sha}"
                )
            )

        await deps.event_store.append(
            process_id,
            CodeRepositoryIndexed(
                branch=code_version.branch,
                commit_sha=code_version.commit_sha,
                stats=stats,
                knowledge_base_id=settings.knowledge_base_id,
                process_id=process_id,
                occurred_at=clock.now(),
            ),
        )
    except GitValidationError as e:
        await deps.event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=settings.repo_url,
                error_type=e.error_type,
                error_message=e.message,
                knowledge_base_id=settings.knowledge_base_id,
                process_id=process_id,
                occurred_at=clock.now(),
            ),
        )
        raise
    except Exception as e:
        await deps.event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=settings.repo_url,
                error_type="unexpected_error",
                error_message=str(e),
                knowledge_base_id=settings.knowledge_base_id,
                process_id=process_id,
                occurred_at=clock.now(),
            ),
        )
        raise
    return process_id


async def _init_dependencies(
    settings: IndexRepositoryCommandSettings,
) -> IndexRepositoryDependencies:
    event_store = await init_event_store(
        database_url=settings.database_url,
        queue_url=settings.process_queue_url,
        webhook_base_url=settings.webhook_base_url,
    )
    git_helper = GitHelper.of(
        git_settings=GitSettings(
            repository_url=settings.repo_url, access_token=settings.access_token or ""
        )
    )
    indexer = OpenAIVectorStoreRepositoryIndexer()
    return IndexRepositoryDependencies(
        event_store=event_store,
        git_helper=git_helper,
        indexer=indexer,
        clock=UTCSystemClock(),
    )


async def _resolve_from_commit_sha(
    event_store: EventStore, settings: IndexRepositoryCommandSettings
) -> str | None:
    if settings.from_commit_sha:
        return settings.from_commit_sha

    if not settings.process_id:
        return None

    events = await event_store.get(settings.process_id)
    last_indexed = most_recent_event(events, CodeRepositoryIndexed)
    return last_indexed.commit_sha if last_indexed else None
