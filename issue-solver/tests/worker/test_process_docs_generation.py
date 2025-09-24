import shutil
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from issue_solver.agents.docs_prompts import suggested_docs_prompts
from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    DocumentingAgent,
)
from issue_solver.git_operations.git_helper import GitHelper
from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeRepository,
    KnowledgeBase,
)
from issue_solver.worker.messages_processing import process_event_message
from issue_solver.worker.dependencies import Dependencies
from tests.controllable_clock import ControllableClock
from tests.examples.happy_path_persona import BriceDeNice


@pytest.mark.asyncio
async def test_process_docs_generation_should_work(
    event_store,
    time_under_control: ControllableClock,
    knowledge_repo: KnowledgeRepository,
):
    # Given
    git_helper = Mock(spec=GitHelper)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    docs_agent = AsyncMock(spec=DocumentingAgent)
    process_id = "a1processid"
    id_generator = Mock()
    id_generator.new.return_value = process_id
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )

    temp_repo_directory = f"/tmp/repo/{process_id}"
    kb_id = repo_connected.knowledge_base_id
    temp_documentation_directory = Path(temp_repo_directory).joinpath(kb_id)
    init_docs_directory(temp_documentation_directory, "adrs")
    docs_agent.generate_documentation.side_effect = (
        lambda repo_path, knowledge_base_id, output_path, docs_prompts, process_id: (
            temp_documentation_directory.joinpath(
                "domain_events_glossary.md"
            ).write_text("# Domain Events Glossary\n"),
            temp_documentation_directory.joinpath("adrs/adr001.md").write_text(
                "# ADR 001 - Sample Architecture Decision Record\n"
            ),
            temp_documentation_directory.joinpath(
                "undesirable_doc_not_md.html"
            ).write_text("# This doc should be ignored as it is not markdown\n"),
        )
    )
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()

    # When
    await process_event_message(
        repo_indexed,
        dependencies=Dependencies(
            event_store,
            git_helper,
            coding_agent,
            knowledge_repo,
            time_under_control,
            id_generator=id_generator,
            docs_agent=docs_agent,
        ),
    )

    # Then
    git_helper.clone_repository.assert_called_once_with(
        url=repo_connected.url,
        access_token=repo_connected.access_token,
        to_path=Path(temp_repo_directory),
    )
    docs_agent.generate_documentation.assert_called_once_with(
        repo_path=Path(temp_repo_directory),
        knowledge_base_id=kb_id,
        output_path=Path(temp_repo_directory).joinpath(kb_id),
        docs_prompts=suggested_docs_prompts(),
        process_id=process_id,
    )
    kb_key = KnowledgeBase(id=kb_id, version=repo_indexed.commit_sha)
    assert knowledge_repo.contains(kb_key, "domain_events_glossary.md")
    assert knowledge_repo.contains(kb_key, "adrs/adr001.md"), (
        f"expected adrs/adr001.md in {knowledge_repo.list_entries(kb_key)}"
    )
    assert not knowledge_repo.contains(kb_key, "undesirable_doc_not_md.html")


def init_docs_directory(temp_documentation_directory: Path, *subdirs: str):
    if temp_documentation_directory.exists():
        shutil.rmtree(temp_documentation_directory)
    temp_documentation_directory.mkdir(parents=True, exist_ok=True)
    for subdir in subdirs:
        temp_documentation_directory.joinpath(subdir).mkdir(parents=True, exist_ok=True)
