import shutil
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    DocumentingAgent,
)
from issue_solver.events.domain import (
    DocumentationGenerationRequested,
    DocumentationGenerationCompleted,
    DocumentationGenerationFailed,
)
from issue_solver.events.auto_documentation import load_auto_documentation_setup
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
async def test_generate_docs_should_enqueue_events_for_each_prompt(
    event_store,
    time_under_control: ControllableClock,
    knowledge_repo: KnowledgeRepository,
):
    # Given
    git_helper = Mock(spec=GitHelper)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    docs_agent = AsyncMock(spec=DocumentingAgent)
    initial_process_id = "a1processid"
    child_ids = ["child-1", "child-2", "child-3", "child-4"]
    id_generator = Mock()
    id_generator.new.side_effect = [initial_process_id, *child_ids]
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )

    temp_repo_directory = f"/tmp/repo/{initial_process_id}"
    kb_id = repo_connected.knowledge_base_id
    temp_documentation_directory = Path(temp_repo_directory).joinpath(kb_id)
    init_docs_directory(temp_documentation_directory, "adrs")
    git_helper.clone_repository.side_effect = (
        lambda url, access_token, to_path: init_docs_directory(
            Path(to_path).joinpath(kb_id), "adrs"
        )
    )
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
        BriceDeNice.has_defined_additional_documentation_prompts(),
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
    docs_agent.generate_documentation.assert_not_called()
    requests = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationGenerationRequested
    )
    expected_prompts = (
        BriceDeNice.defined_prompts_for_documentation()
        | BriceDeNice.defined_additional_prompts_for_documentation()
    )
    assert len(requests) == len(expected_prompts)
    assert {req.prompt_id for req in requests} == set(expected_prompts.keys())
    auto_doc_setup = await load_auto_documentation_setup(event_store, kb_id)
    assert auto_doc_setup.last_process_id is not None
    for req in requests:
        assert req.prompt_description == expected_prompts[req.prompt_id]
        assert req.parent_process_id == auto_doc_setup.last_process_id
        assert req.code_version == repo_indexed.commit_sha


@pytest.mark.asyncio
async def test_generate_docs_should_not_enqueue_events_when_no_prompts_defined(
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
    requests = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationGenerationRequested
    )
    assert requests == []


@pytest.mark.asyncio
async def test_generate_docs_should_use_latest_prompt_configuration(
    event_store,
    time_under_control: ControllableClock,
    knowledge_repo: KnowledgeRepository,
):
    # Given
    git_helper = Mock(spec=GitHelper)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    docs_agent = AsyncMock(spec=DocumentingAgent)
    id_generator = Mock()
    id_generator.new.side_effect = [
        "a1processid",
        "child-1",
        "child-2",
        "child-3",
        "child-4",
    ]
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
    kb_id = repo_connected.knowledge_base_id
    requests = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationGenerationRequested
    )
    expected_prompts = (
        BriceDeNice.defined_prompts_for_documentation()
        | BriceDeNice.defined_additional_prompts_for_documentation()
    )
    assert {req.prompt_id for req in requests} == set(expected_prompts.keys())
    auto_doc_setup = await load_auto_documentation_setup(event_store, kb_id)
    assert auto_doc_setup.last_process_id is not None
    for req in requests:
        assert req.parent_process_id == auto_doc_setup.last_process_id


@pytest.mark.asyncio
async def test_generate_docs_should_emit_requests_using_changed_prompts(
    event_store,
    time_under_control: ControllableClock,
    knowledge_repo: KnowledgeRepository,
):
    # Given
    git_helper = Mock(spec=GitHelper)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    docs_agent = AsyncMock(spec=DocumentingAgent)
    id_generator = Mock()
    id_generator.new.side_effect = [
        "a1processid",
        "child-1",
        "child-2",
        "child-3",
        "child-4",
    ]
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
    kb_id = repo_connected.knowledge_base_id
    requests = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationGenerationRequested
    )
    expected_docs_prompts = (
        BriceDeNice.has_changed_documentation_prompts().docs_prompts
        | BriceDeNice.defined_additional_prompts_for_documentation()
    )
    assert {req.prompt_id for req in requests} == set(expected_docs_prompts.keys())
    auto_doc_setup = await load_auto_documentation_setup(event_store, kb_id)
    assert auto_doc_setup.last_process_id is not None
    for req in requests:
        assert req.prompt_description == expected_docs_prompts[req.prompt_id]
        assert req.parent_process_id == auto_doc_setup.last_process_id


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
async def test_generate_docs_should_load_existing_repo_markdown(
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
    id_generator.new.side_effect = [process_id, "child-1", "child-2"]

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
    docs_agent.generate_documentation.assert_not_called()


@pytest.mark.asyncio
async def test_process_documentation_generation_request_should_generate_docs(
    event_store,
    time_under_control: ControllableClock,
    knowledge_repo: KnowledgeRepository,
):
    git_helper = Mock(spec=GitHelper)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    docs_agent = AsyncMock(spec=DocumentingAgent)
    child_process_id = "doc-child-1"

    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )

    kb_id = repo_connected.knowledge_base_id
    prompt = {"domain_events_glossary": "Write glossary"}

    temp_documentation_directory = (
        Path(f"/tmp/repo/{child_process_id}").joinpath(kb_id)
    )
    init_docs_directory(temp_documentation_directory)
    git_helper.clone_repository.side_effect = (
        lambda url, access_token, to_path: init_docs_directory(
            Path(to_path).joinpath(kb_id)
        )
    )
    docs_agent.generate_documentation.side_effect = (
        lambda repo_path, knowledge_base_id, output_path, docs_prompts, process_id: (
            temp_documentation_directory.joinpath(
                "domain_events_glossary.md"
            ).write_text("# Domain Events Glossary\n"),
        )
    )

    request_event = DocumentationGenerationRequested(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        prompt_description="Write glossary",
        code_version="commit-sha",
        parent_process_id=BriceDeNice.doc_configuration_process_id(),
        process_id=child_process_id,
        occurred_at=time_under_control.now(),
    )

    await process_event_message(
        request_event,
        dependencies=Dependencies(
            event_store,
            git_helper,
            coding_agent,
            knowledge_repo,
            time_under_control,
            docs_agent=docs_agent,
        ),
    )

    docs_agent.generate_documentation.assert_called_once()
    kb_key = KnowledgeBase(id=kb_id, version="commit-sha")
    assert knowledge_repo.contains(kb_key, "domain_events_glossary.md")
    assert knowledge_repo.get_origin(kb_key, "domain_events_glossary.md") == "auto"
    child_events = await event_store.get(child_process_id)
    assert isinstance(child_events[-1], DocumentationGenerationCompleted)
    assert child_events[-1].generated_documents == ["domain_events_glossary.md"]


@pytest.mark.asyncio
async def test_process_documentation_generation_request_should_emit_failure_event(
    event_store,
    time_under_control: ControllableClock,
    knowledge_repo: KnowledgeRepository,
):
    git_helper = Mock(spec=GitHelper)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    docs_agent = AsyncMock(spec=DocumentingAgent)
    docs_agent.generate_documentation.side_effect = RuntimeError("boom")

    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )

    request_event = DocumentationGenerationRequested(
        knowledge_base_id=repo_connected.knowledge_base_id,
        prompt_id="overview",
        prompt_description="Write overview",
        code_version="commit-sha",
        parent_process_id=BriceDeNice.doc_configuration_process_id(),
        process_id="doc-child-failure",
        occurred_at=time_under_control.now(),
    )

    await process_event_message(
        request_event,
        dependencies=Dependencies(
            event_store,
            git_helper,
            coding_agent,
            knowledge_repo,
            time_under_control,
            docs_agent=docs_agent,
        ),
    )

    child_events = await event_store.get("doc-child-failure")
    assert isinstance(child_events[-1], DocumentationGenerationFailed)
    assert "boom" in child_events[-1].error_message
