import shutil
from pathlib import Path
import pytest
from issue_solver.events.domain import (
    DocumentationGenerationRequested,
    DocumentationGenerationStarted,
    DocumentationGenerationCompleted,
    DocumentationGenerationFailed,
    CodeRepositoryConnected,
    DocumentationPromptsDefined,
    DocumentationPromptsRemoved,
)
from issue_solver.events.event_store import EventStore
from issue_solver.worker.documenting.knowledge_repository import KnowledgeBase
from issue_solver.worker.messages_processing import process_event_message
from issue_solver.worker.dependencies import Dependencies
from tests.controllable_clock import ControllableClock
from tests.examples.happy_path_persona import BriceDeNice


OLD_DOC_TEXT = "# Domain Events (old)\n"
NEW_DOC_TEXT = "# Domain Events (updated)\n"


def seed_repo_with_kb(kb_id: str):
    def _seed(url, access_token, to_path):
        Path(to_path).joinpath(kb_id).mkdir(parents=True, exist_ok=True)

    return _seed


def docs_agent_update_with_capture(capture: list[str | None], new_text: str):
    def _update(repo_path, knowledge_base_id, output_path, docs_prompts, process_id):
        output_path.mkdir(parents=True, exist_ok=True)
        raw_name = next(iter(docs_prompts.keys()))
        doc_name = raw_name if raw_name.endswith(".md") else f"{raw_name}.md"
        seeded = output_path.joinpath(doc_name)
        captured_text = seeded.read_text() if seeded.exists() else None
        capture.append(captured_text)
        seeded.write_text(new_text)

    return _update


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
    requested_generation_ids = ["child-1", "child-2", "child-3", "child-4"]
    id_generator.new.side_effect = [initial_process_id, *requested_generation_ids]
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
        run_id = initial_process_id
        expected_requests.append(
            DocumentationGenerationRequested(
                knowledge_base_id=kb_id,
                prompt_id=prompt_id,
                prompt_description=prompt_description,
                code_version=repo_indexed.commit_sha,
                run_id=run_id,
                process_id=requested_generation_ids[index],
                occurred_at=run_started_at,
                mode="update",
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
    requested_generation_ids = ["child-1", "child-2"]
    run_id = "a1processid"
    id_generator.new.side_effect = [run_id, *requested_generation_ids]
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
    expected_requests: list[DocumentationGenerationRequested] = []
    for index, (prompt_id, description) in enumerate(base_prompts.items()):
        child_id = requested_generation_ids[index]
        expected_requests.append(
            DocumentationGenerationRequested(
                knowledge_base_id=kb_id,
                prompt_id=prompt_id,
                prompt_description=description,
                code_version=repo_indexed.commit_sha,
                run_id=run_id,
                process_id=child_id,
                occurred_at=run_started_at,
                mode="update",
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
    run_id = "a1processid"
    expected_requests: list[DocumentationGenerationRequested] = []
    for index, (prompt_id, prompt_description) in enumerate(updated_prompts.items()):
        child_id = child_ids[index]
        expected_requests.append(
            DocumentationGenerationRequested(
                knowledge_base_id=kb_id,
                prompt_id=prompt_id,
                prompt_description=prompt_description,
                code_version=repo_indexed.commit_sha,
                run_id=run_id,
                process_id=child_id,
                occurred_at=run_started_at,
                mode="update",
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
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()
    kb_key = KnowledgeBase(
        id=repo_connected.knowledge_base_id,
        version=repo_indexed.commit_sha,
    )

    assert knowledge_repo.contains(kb_key, "README.md")
    assert knowledge_repo.get_origin(kb_key, "README.md") == "repo"
    assert knowledge_repo.get_metadata(kb_key, "README.md") == {
        "origin": "repo",
        "process_id": repo_indexed.process_id,
    }
    assert knowledge_repo.contains(kb_key, "docs/runbook.md")
    assert knowledge_repo.get_origin(kb_key, "docs/runbook.md") == "repo"
    assert knowledge_repo.get_metadata(kb_key, "docs/runbook.md") == {
        "origin": "repo",
        "process_id": repo_indexed.process_id,
    }
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
    run_id = "generation-run-001"
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
        run_id=run_id,
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
    assert knowledge_repo.get_metadata(kb_key, "domain_events_glossary.md") == {
        "origin": "auto",
        "process_id": child_process_id,
    }

    child_events = await event_store.get(child_process_id)
    expected_started = DocumentationGenerationStarted(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        code_version="commit-sha",
        run_id=run_id,
        process_id=child_process_id,
        occurred_at=time_under_control.now(),
    )
    expected_completion = DocumentationGenerationCompleted(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        code_version="commit-sha",
        run_id=run_id,
        generated_documents=["domain_events_glossary.md"],
        process_id=child_process_id,
        occurred_at=time_under_control.now(),
    )
    assert child_events == [request_event, expected_started, expected_completion]


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
    run_id = "generation-run-002"
    child_process_id = "doc-child-failure"
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
        run_id=run_id,
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
    child_events = await event_store.get(child_process_id)
    expected_started = DocumentationGenerationStarted(
        knowledge_base_id=repo_connected.knowledge_base_id,
        prompt_id="overview",
        code_version="commit-sha",
        run_id=run_id,
        process_id=child_process_id,
        occurred_at=child_events[1].occurred_at,
    )
    expected_failure = DocumentationGenerationFailed(
        knowledge_base_id=repo_connected.knowledge_base_id,
        prompt_id="overview",
        code_version="commit-sha",
        run_id=run_id,
        error_message="boom",
        process_id=child_process_id,
        occurred_at=request_event.occurred_at,
    )
    assert child_events == [request_event, expected_started, expected_failure]


@pytest.mark.asyncio
async def test_process_documentation_generation_request_should_error_when_docs_agent_missing(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    coding_agent,
):
    # Given
    run_id = "generation-run-003"
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
        run_id=run_id,
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


@pytest.mark.asyncio
async def test_generate_docs_should_request_update_mode_by_default(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    docs_agent,
    id_generator,
    worker_dependencies,
):
    # Given
    run_id = "run-default-mode"
    child_ids = ["child-a", "child-b"]
    id_generator.new.side_effect = [run_id, *child_ids]
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        BriceDeNice.first_repo_integration_process_id(), repo_connected
    )
    await event_store.append(
        BriceDeNice.doc_configuration_process_id(),
        BriceDeNice.has_defined_documentation_prompts(),
    )
    repo_indexed = BriceDeNice.got_his_first_repo_indexed()

    # When
    await process_event_message(repo_indexed, dependencies=worker_dependencies)

    # Then
    requests = await event_store.find(
        {"knowledge_base_id": repo_connected.knowledge_base_id},
        DocumentationGenerationRequested,
    )
    assert requests, "documentation requests should be emitted"
    assert all(getattr(req, "mode", None) == "update" for req in requests)


@pytest.mark.asyncio
async def test_process_documentation_generation_request_complete_mode_should_skip_seed(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    coding_agent,
    docs_agent,
):
    # Given
    kb_id = "kb-auto-doc-complete"
    old_version = "commit-old"
    new_version = "commit-new"
    observed_seed_texts: list[str | None] = []

    repo_connected = CodeRepositoryConnected(
        url="https://example.com/repo.git",
        access_token="token",
        user_id="user-123",
        space_id="space-123",
        knowledge_base_id=kb_id,
        process_id="conn-process-id",
        occurred_at=time_under_control.now(),
        token_permissions=None,
    )
    await event_store.append(repo_connected.process_id, repo_connected)

    knowledge_repo.add(
        KnowledgeBase(kb_id, old_version),
        "domain_events_glossary.md",
        OLD_DOC_TEXT,
        metadata={"origin": "auto", "process_id": "old-process"},
    )

    git_helper.clone_repository.side_effect = seed_repo_with_kb(kb_id)
    docs_agent.generate_documentation.side_effect = docs_agent_update_with_capture(
        observed_seed_texts, NEW_DOC_TEXT
    )

    request_event = DocumentationGenerationRequested(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        prompt_description="Write glossary",
        code_version=new_version,
        run_id="run-complete",
        process_id="doc-child-complete",
        occurred_at=time_under_control.now(),
        mode="complete",
    )
    await event_store.append("doc-child-complete", request_event)

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
    assert observed_seed_texts == [None]


@pytest.mark.asyncio
async def test_update_mode_should_skip_seed_when_prompt_changed(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    coding_agent,
    docs_agent,
):
    # Given
    kb_id = "kb-auto-doc-update-changed"
    old_version = "commit-old"
    new_version = "commit-new"
    observed_seed_texts: list[str | None] = []

    repo_connected = CodeRepositoryConnected(
        url="https://example.com/repo.git",
        access_token="token",
        user_id="user-123",
        space_id="space-123",
        knowledge_base_id=kb_id,
        process_id="conn-process-id",
        occurred_at=time_under_control.now(),
        token_permissions=None,
    )
    completed = DocumentationGenerationCompleted(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        code_version=old_version,
        run_id="prior-run",
        generated_documents=["domain_events_glossary.md"],
        process_id="prior-process",
        occurred_at=time_under_control.now(),
    )
    prompt_defined = DocumentationPromptsDefined(
        knowledge_base_id=kb_id,
        user_id="user-123",
        docs_prompts={"domain_events_glossary": "Old prompt"},
        process_id="def-process",
        occurred_at=time_under_control.now(),
    )
    prompt_changed = DocumentationPromptsRemoved(
        knowledge_base_id=kb_id,
        user_id="user-123",
        prompt_ids={"domain_events_glossary"},
        process_id="removal-process",
        occurred_at=time_under_control.now(),
    )
    awaited_definition = DocumentationPromptsDefined(
        knowledge_base_id=kb_id,
        user_id="user-123",
        docs_prompts={"domain_events_glossary": "New different prompt"},
        process_id="def-process-2",
        occurred_at=time_under_control.now(),
    )
    await event_store.append(
        repo_connected.process_id,
        repo_connected,
        prompt_defined,
        completed,
        prompt_changed,
        awaited_definition,
    )

    knowledge_repo.add(
        KnowledgeBase(kb_id, old_version),
        "domain_events_glossary.md",
        OLD_DOC_TEXT,
        metadata={"origin": "auto", "process_id": "old-process"},
    )

    git_helper.clone_repository.side_effect = seed_repo_with_kb(kb_id)
    docs_agent.generate_documentation.side_effect = docs_agent_update_with_capture(
        observed_seed_texts, NEW_DOC_TEXT
    )

    request_event = DocumentationGenerationRequested(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        prompt_description="New different prompt",
        code_version=new_version,
        run_id="run-update-changed",
        process_id="doc-child-update-changed",
        occurred_at=time_under_control.now(),
        mode="update",
    )
    await event_store.append("doc-child-update-changed", request_event)

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
    assert observed_seed_texts == [None]


@pytest.mark.asyncio
async def test_process_documentation_generation_request_update_mode_should_reuse_previous_docs(
    event_store: EventStore,
    time_under_control: ControllableClock,
    knowledge_repo,
    git_helper,
    coding_agent,
    docs_agent,
):
    # Given
    kb_id = "kb-auto-doc-update"
    old_version = "commit-old"
    new_version = "commit-new"
    run_id = "generation-run-update"
    child_process_id = "doc-child-update"
    observed_seed_texts: list[str | None] = []

    completed = DocumentationGenerationCompleted(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        code_version=old_version,
        run_id="prior-run",
        generated_documents=["domain_events_glossary.md"],
        process_id="prior-process",
        occurred_at=time_under_control.now(),
    )
    prompt_defined = DocumentationPromptsDefined(
        knowledge_base_id=kb_id,
        user_id="user-123",
        docs_prompts={"domain_events_glossary": "Write glossary"},
        process_id="def-process",
        occurred_at=time_under_control.now(),
    )
    repo_connected = CodeRepositoryConnected(
        url="https://example.com/repo.git",
        access_token="token",
        user_id="user-123",
        space_id="space-123",
        knowledge_base_id=kb_id,
        process_id="conn-process-id",
        occurred_at=time_under_control.now(),
        token_permissions=None,
    )
    await event_store.append(
        repo_connected.process_id, repo_connected, prompt_defined, completed
    )

    knowledge_repo.add(
        KnowledgeBase(kb_id, old_version),
        "domain_events_glossary.md",
        OLD_DOC_TEXT,
        metadata={"origin": "auto", "process_id": "old-process"},
    )

    git_helper.clone_repository.side_effect = seed_repo_with_kb(kb_id)
    docs_agent.generate_documentation.side_effect = docs_agent_update_with_capture(
        observed_seed_texts, NEW_DOC_TEXT
    )

    request_event = DocumentationGenerationRequested(
        knowledge_base_id=kb_id,
        prompt_id="domain_events_glossary",
        prompt_description="Write glossary",
        code_version=new_version,
        run_id=run_id,
        process_id=child_process_id,
        occurred_at=time_under_control.now(),
        mode="update",
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
    kb_key_new = KnowledgeBase(id=kb_id, version=new_version)
    assert knowledge_repo.contains(kb_key_new, "domain_events_glossary.md")
    assert (
        knowledge_repo.get_content(kb_key_new, "domain_events_glossary.md")
        == NEW_DOC_TEXT
    )
    assert knowledge_repo.get_origin(kb_key_new, "domain_events_glossary.md") == "auto"

    kb_key_old = KnowledgeBase(id=kb_id, version=old_version)
    assert (
        knowledge_repo.get_content(kb_key_old, "domain_events_glossary.md")
        == OLD_DOC_TEXT
    )
    assert observed_seed_texts == [OLD_DOC_TEXT]
