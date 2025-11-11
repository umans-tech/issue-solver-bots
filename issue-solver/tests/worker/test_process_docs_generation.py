import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    DocumentingAgent,
)
from issue_solver.events.domain import DocumentationPromptsDefined
from issue_solver.git_operations.git_helper import GitHelper
from issue_solver.worker.documenting.auto import get_prompts_for_doc_to_generate
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
    git_helper.clone_repository.side_effect = (
        lambda url, access_token, to_path: init_docs_directory(
            Path(to_path).joinpath(kb_id), "adrs"
        )
    )
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
    user_defined_prompts = BriceDeNice.defined_prompts_for_documentation()
    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
    )

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
        docs_prompts=user_defined_prompts,
        process_id=process_id,
    )
    kb_key = KnowledgeBase(id=kb_id, version=repo_indexed.commit_sha)
    assert knowledge_repo.contains(kb_key, "domain_events_glossary.md")
    assert knowledge_repo.get_origin(kb_key, "domain_events_glossary.md") == "auto"
    assert knowledge_repo.contains(kb_key, "adrs/adr001.md"), (
        f"expected adrs/adr001.md in {knowledge_repo.list_entries(kb_key)}"
    )
    assert knowledge_repo.get_origin(kb_key, "adrs/adr001.md") == "auto"
    assert not knowledge_repo.contains(kb_key, "undesirable_doc_not_md.html")


@pytest.mark.asyncio
async def test_process_docs_generation_should_not_generate_any_docs_when_no_prompts_defined(
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

    kb_id = repo_connected.knowledge_base_id

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
    docs_agent.generate_documentation.assert_not_called()
    kb_key = KnowledgeBase(id=kb_id, version=repo_indexed.commit_sha)
    assert knowledge_repo.list_entries(kb_key) == []


@pytest.mark.asyncio
async def test_process_docs_generation_should_generate_docs_when_multiple_prompts_defined(
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

    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
        BriceDeNice.has_defined_additional_documentation_prompts(),
    )

    # When
    await process_event_message(
        BriceDeNice.got_his_first_repo_indexed(),
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
    temp_repo_directory = f"/tmp/repo/{process_id}"
    kb_id = repo_connected.knowledge_base_id
    docs_agent.generate_documentation.assert_called_once_with(
        repo_path=Path(temp_repo_directory),
        knowledge_base_id=kb_id,
        output_path=Path(temp_repo_directory).joinpath(kb_id),
        docs_prompts=BriceDeNice.defined_prompts_for_documentation()
        | BriceDeNice.defined_additional_prompts_for_documentation(),
        process_id=process_id,
    )


@pytest.mark.asyncio
async def test_process_docs_generation_should_generate_docs_when_defined_prompts_are_changed(
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

    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
        BriceDeNice.has_defined_additional_documentation_prompts(),
        BriceDeNice.has_changed_documentation_prompts(),
    )

    # When
    await process_event_message(
        BriceDeNice.got_his_first_repo_indexed(),
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
    temp_repo_directory = f"/tmp/repo/{process_id}"
    kb_id = repo_connected.knowledge_base_id
    expected_docs_prompts = (
        BriceDeNice.has_changed_documentation_prompts().docs_prompts
        | BriceDeNice.defined_additional_prompts_for_documentation()
    )
    docs_agent.generate_documentation.assert_called_once_with(
        repo_path=Path(temp_repo_directory),
        knowledge_base_id=kb_id,
        output_path=Path(temp_repo_directory).joinpath(kb_id),
        docs_prompts=expected_docs_prompts,
        process_id=process_id,
    )


def init_docs_directory(temp_documentation_directory: Path, *subdirs: str):
    if temp_documentation_directory.exists():
        shutil.rmtree(temp_documentation_directory)
    temp_documentation_directory.mkdir(parents=True, exist_ok=True)
    for subdir in subdirs:
        temp_documentation_directory.joinpath(subdir).mkdir(parents=True, exist_ok=True)


def seed_repository_markdown(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    target.joinpath("README.md").write_text("# Repository Readme\n")
    docs_dir = target.joinpath("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.joinpath("runbook.md").write_text("# Runbook\nSteps...\n")
    target.joinpath("docs", "notes.txt").write_text("not markdown")
    target.joinpath("LICENSE").write_text("MIT")


@pytest.mark.asyncio
async def test_process_docs_generation_should_load_existing_repo_markdown(
    event_store,
    time_under_control: ControllableClock,
    knowledge_repo: KnowledgeRepository,
):
    # Given
    git_helper = Mock(spec=GitHelper)
    docs_agent = AsyncMock(spec=DocumentingAgent)
    docs_agent.generate_documentation.return_value = None
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    process_id = "seeded-process"
    id_generator = Mock()
    id_generator.new.return_value = process_id

    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )
    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
    )

    git_helper.clone_repository.side_effect = (
        lambda url, access_token, to_path: seed_repository_markdown(Path(to_path))
    )

    # When
    await process_event_message(
        BriceDeNice.got_his_first_repo_indexed(),
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
    kb_key = KnowledgeBase(
        id=repo_connected.knowledge_base_id,
        version=BriceDeNice.got_his_first_repo_indexed().commit_sha,
    )

    assert knowledge_repo.contains(kb_key, "README.md")
    assert knowledge_repo.get_origin(kb_key, "README.md") == "repo"
    assert knowledge_repo.contains(kb_key, "docs/runbook.md")
    assert knowledge_repo.get_origin(kb_key, "docs/runbook.md") == "repo"
    assert not knowledge_repo.contains(kb_key, "docs/notes.txt")


@pytest.mark.asyncio
async def test_get_prompts_for_doc_to_generate_should_ignore_blank_entries(event_store):
    knowledge_base_id = "brice-kb-001"
    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
    )
    removal_event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id="doc-bot",
        docs_prompts={"domain_events_glossary": ""},
        process_id="doc-removal-process",
        occurred_at=datetime.fromisoformat("2025-02-01T10:00:00Z"),
    )
    await event_store.append(removal_event.process_id, removal_event)

    prompts = await get_prompts_for_doc_to_generate(event_store, knowledge_base_id)

    assert "domain_events_glossary" not in prompts
