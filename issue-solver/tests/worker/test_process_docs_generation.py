import shutil
from pathlib import Path
import pytest
from issue_solver.events.domain import (
    DocumentationGenerationRequested,
    DocumentationGenerationCompleted,
    DocumentationGenerationFailed,
)
from issue_solver.events.event_store import EventStore
from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeBase,
)
from issue_solver.worker.messages_processing import process_event_message
from issue_solver.worker.dependencies import Dependencies
from tests.controllable_clock import ControllableClock
from tests.examples.happy_path_persona import BriceDeNice


@pytest.mark.asyncio
async def test_generate_docs_should_request_each_prompt_individually(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    docs_agent,
    id_generator,
    worker_dependencies,
):
    # Given
    initial_process_id = "a1processid"
    child_ids = ["child-1", "child-2", "child-3", "child-4"]
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
    run_started_at = time_under_control.now()
    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
        BriceDeNice.has_defined_additional_documentation_prompts(),
    )

    # When
    await process_event_message(
        repo_indexed,
        dependencies=worker_dependencies,
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
    expected_requests: list[DocumentationGenerationRequested] = []
    for index, (prompt_id, prompt_description) in enumerate(expected_prompts.items()):
        child_id = child_ids[index]
        expected_requests.append(
            DocumentationGenerationRequested(
                knowledge_base_id=kb_id,
                prompt_id=prompt_id,
                prompt_description=prompt_description,
                code_version=repo_indexed.commit_sha,
                parent_process_id=BriceDeNice.doc_configuration_process_id(),
                process_id=child_id,
                occurred_at=run_started_at,
            )
        )
    assert requests == expected_requests


@pytest.mark.asyncio
async def test_generate_docs_should_skip_when_no_prompts_defined(
    event_store: EventStore,
    knowledge_repo,
    git_helper,
    docs_agent,
    id_generator,
    worker_dependencies,
):
    # Given
    id_generator.new.return_value = "a1processid"
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )

    kb_id = repo_connected.knowledge_base_id

    repo_indexed = BriceDeNice.got_his_first_repo_indexed()

    # When
    await process_event_message(repo_indexed, dependencies=worker_dependencies)

    # Then
    docs_agent.generate_documentation.assert_not_called()
    requests = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationGenerationRequested
    )
    assert requests == []


@pytest.mark.asyncio
async def test_generate_docs_should_error_when_docs_agent_missing(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    coding_agent,
    id_generator,
):
    # Given
    id_generator.new.return_value = "a1processid"
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )
    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
    )
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()

    # When / Then
    with pytest.raises(RuntimeError, match="Docs agent is not configured"):
        await process_event_message(
            repo_indexed,
            dependencies=Dependencies(
                event_store,
                git_helper,
                coding_agent,
                knowledge_repo,
                time_under_control,
                id_generator=id_generator,
                docs_agent=None,
            ),
        )


@pytest.mark.asyncio
async def test_generate_docs_should_request_using_latest_prompts(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    docs_agent,
    id_generator,
    worker_dependencies,
):
    # Given
    child_ids = ["child-1", "child-2"]
    id_generator.new.side_effect = ["a1processid", *child_ids]
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )

    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
    )

    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    run_started_at = time_under_control.now()

    # When
    await process_event_message(repo_indexed, dependencies=worker_dependencies)

    # Then
    kb_id = repo_connected.knowledge_base_id
    requests = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationGenerationRequested
    )
    base_prompts = BriceDeNice.defined_prompts_for_documentation()
    parent_process_id = BriceDeNice.doc_configuration_process_id()
    expected_requests: list[DocumentationGenerationRequested] = []
    for index, (prompt_id, description) in enumerate(base_prompts.items()):
        child_id = child_ids[index]
        expected_requests.append(
            DocumentationGenerationRequested(
                knowledge_base_id=kb_id,
                prompt_id=prompt_id,
                prompt_description=description,
                code_version=repo_indexed.commit_sha,
                parent_process_id=parent_process_id,
                process_id=child_id,
                occurred_at=run_started_at,
            )
        )
    assert requests == expected_requests


@pytest.mark.asyncio
async def test_generate_docs_should_request_changed_prompts(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    docs_agent,
    id_generator,
    worker_dependencies,
):
    # Given
    child_ids = ["child-1", "child-2", "child-3", "child-4"]
    id_generator.new.side_effect = ["a1processid", *child_ids]
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

    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    run_started_at = time_under_control.now()

    # When
    await process_event_message(repo_indexed, dependencies=worker_dependencies)

    # Then
    kb_id = repo_connected.knowledge_base_id
    requests = await event_store.find(
        {"knowledge_base_id": kb_id}, DocumentationGenerationRequested
    )
    changed_prompts = BriceDeNice.has_changed_documentation_prompts().docs_prompts
    additional_prompts = BriceDeNice.defined_additional_prompts_for_documentation()
    updated_prompts = changed_prompts | additional_prompts
    parent_process_id = BriceDeNice.has_changed_documentation_prompts().process_id
    expected_requests: list[DocumentationGenerationRequested] = []
    for index, (prompt_id, prompt_description) in enumerate(updated_prompts.items()):
        child_id = child_ids[index]
        expected_requests.append(
            DocumentationGenerationRequested(
                knowledge_base_id=kb_id,
                prompt_id=prompt_id,
                prompt_description=prompt_description,
                code_version=repo_indexed.commit_sha,
                parent_process_id=parent_process_id,
                process_id=child_id,
                occurred_at=run_started_at,
            )
        )
    assert requests == expected_requests


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
async def test_generate_docs_should_import_existing_repo_markdown(
    event_store: EventStore,
    knowledge_repo,
    git_helper,
    docs_agent,
    id_generator,
    worker_dependencies,
):
    # Given
    process_id = "seeded-process"
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
        dependencies=worker_dependencies,
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
async def test_process_documentation_generation_request_should_store_outputs(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    coding_agent,
    docs_agent,
):
    # Given
    child_process_id = "doc-child-1"
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(),
        repo_connected,
    )
    kb_id = repo_connected.knowledge_base_id
    temp_documentation_directory = Path(f"/tmp/repo/{child_process_id}").joinpath(kb_id)
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
    await event_store.append(child_process_id, request_event)

    # When
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

    # Then
    docs_agent.generate_documentation.assert_called_once()
    kb_key = KnowledgeBase(id=kb_id, version="commit-sha")
    assert knowledge_repo.contains(kb_key, "domain_events_glossary.md")
    assert knowledge_repo.get_origin(kb_key, "domain_events_glossary.md") == "auto"

    child_events = await event_store.get(child_process_id)
    expected_completion = DocumentationGenerationCompleted(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        code_version="commit-sha",
        parent_process_id=BriceDeNice.doc_configuration_process_id(),
        generated_documents=["domain_events_glossary.md"],
        process_id=child_process_id,
        occurred_at=request_event.occurred_at,
    )
    assert child_events == [request_event, expected_completion]


@pytest.mark.asyncio
async def test_process_documentation_generation_request_should_record_failure(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    coding_agent,
    docs_agent,
):
    # Given
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
    await event_store.append(request_event.process_id, request_event)

    # When
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

    # Then
    child_events = await event_store.get("doc-child-failure")
    expected_failure = DocumentationGenerationFailed(
        knowledge_base_id=repo_connected.knowledge_base_id,
        prompt_id="overview",
        code_version="commit-sha",
        parent_process_id=BriceDeNice.doc_configuration_process_id(),
        error_message="boom",
        process_id="doc-child-failure",
        occurred_at=request_event.occurred_at,
    )
    assert child_events == [request_event, expected_failure]


@pytest.mark.asyncio
async def test_process_documentation_generation_request_should_error_when_docs_agent_missing(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    coding_agent,
):
    # Given
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
        process_id="doc-child-no-agent",
        occurred_at=time_under_control.now(),
    )

    # When / Then
    with pytest.raises(RuntimeError, match="Docs agent is not configured"):
        await process_event_message(
            request_event,
            dependencies=Dependencies(
                event_store,
                git_helper,
                coding_agent,
                knowledge_repo,
                time_under_control,
                docs_agent=None,
            ),
        )
