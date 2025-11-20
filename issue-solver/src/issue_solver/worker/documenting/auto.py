import shutil
from pathlib import Path

from issue_solver.agents.issue_resolving_agent import DocumentingAgent
from issue_solver.events.code_repo_integration import fetch_repo_credentials
from issue_solver.events.domain import (
    CodeRepositoryIndexed,
    DocumentationGenerationRequested,
    DocumentationGenerationStarted,
    DocumentationGenerationCompleted,
    DocumentationGenerationFailed,
    Mode,
)
from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeBase,
    KnowledgeRepository,
    DocRef,
)
from issue_solver.worker.dependencies import Dependencies
from issue_solver.events.auto_documentation import load_auto_documentation_setup
from issue_solver.worker.logging_config import logger


async def generate_docs(
    event: CodeRepositoryIndexed, dependencies: Dependencies
) -> None:
    docs_agent = dependencies.docs_agent
    if not docs_agent:
        raise RuntimeError("Docs agent is not configured")
    repo_credentials = await fetch_repo_credentials(
        event_store=dependencies.event_store,
        knowledge_base_id=event.knowledge_base_id,
    )
    code_version = event.commit_sha
    run_id = dependencies.id_generator.new()
    repo_path = await prepare_repo_path(run_id)
    dependencies.git_client.clone_repository(
        url=repo_credentials.url,
        access_token=repo_credentials.access_token,
        to_path=repo_path,
    )
    load_existing_markdown_documents(
        repo_path=repo_path,
        knowledge_repo=dependencies.knowledge_repository,
        knowledge_base_id=event.knowledge_base_id,
        code_version=code_version,
        process_id=event.process_id,
    )
    auto_doc_setup = await load_auto_documentation_setup(
        dependencies.event_store, event.knowledge_base_id
    )
    if not auto_doc_setup.docs_prompts:
        return

    for prompt_id, prompt_description in auto_doc_setup.docs_prompts.items():
        one_document_generation_process_id = dependencies.id_generator.new()
        await dependencies.event_store.append(
            one_document_generation_process_id,
            DocumentationGenerationRequested(
                knowledge_base_id=event.knowledge_base_id,
                prompt_id=prompt_id,
                prompt_description=prompt_description,
                code_version=code_version,
                run_id=run_id,
                process_id=one_document_generation_process_id,
                occurred_at=dependencies.clock.now(),
                mode="update",
            ),
        )


async def process_documentation_generation_request(
    event: DocumentationGenerationRequested, dependencies: Dependencies
) -> None:
    docs_agent = dependencies.docs_agent
    if not docs_agent:
        raise RuntimeError("Docs agent is not configured")

    repo_credentials = await fetch_repo_credentials(
        event_store=dependencies.event_store,
        knowledge_base_id=event.knowledge_base_id,
    )
    repo_path = await prepare_repo_path(event.process_id)
    dependencies.git_client.clone_repository(
        url=repo_credentials.url,
        access_token=repo_credentials.access_token,
        to_path=repo_path,
    )

    await dependencies.event_store.append(
        event.process_id,
        DocumentationGenerationStarted(
            knowledge_base_id=event.knowledge_base_id,
            prompt_id=event.prompt_id,
            code_version=event.code_version,
            run_id=event.run_id,
            process_id=event.process_id,
            occurred_at=dependencies.clock.now(),
        ),
    )

    try:
        generated_docs = await generate_and_load_docs(
            docs_agent,
            dependencies.knowledge_repository,
            dependencies.event_store,
            event.process_id,
            event.knowledge_base_id,
            event.code_version,
            {event.prompt_id: event.prompt_description},
            mode=event.mode,
        )
    except Exception as exc:
        logger.error(
            "Documentation generation failed for prompt %s in KB %s: %s",
            event.prompt_id,
            event.knowledge_base_id,
            str(exc),
        )
        await dependencies.event_store.append(
            event.process_id,
            DocumentationGenerationFailed(
                knowledge_base_id=event.knowledge_base_id,
                prompt_id=event.prompt_id,
                code_version=event.code_version,
                run_id=event.run_id,
                error_message=str(exc),
                process_id=event.process_id,
                occurred_at=dependencies.clock.now(),
            ),
        )
        return

    await dependencies.event_store.append(
        event.process_id,
        DocumentationGenerationCompleted(
            knowledge_base_id=event.knowledge_base_id,
            prompt_id=event.prompt_id,
            code_version=event.code_version,
            run_id=event.run_id,
            generated_documents=generated_docs,
            process_id=event.process_id,
            occurred_at=dependencies.clock.now(),
        ),
    )


async def prepare_repo_path(process_id: str) -> Path:
    repo_path = Path(f"/tmp/repo/{process_id}")
    if repo_path.exists():
        shutil.rmtree(repo_path)
    return repo_path


async def generate_and_load_docs(
    docs_agent: DocumentingAgent,
    knowledge_repo: KnowledgeRepository,
    event_store,
    process_id: str,
    knowledge_base_id: str,
    code_version: str,
    docs_prompts: dict[str, str],
    mode: Mode = "complete",
) -> list[str]:
    generated_docs_path = Path(f"/tmp/repo/{process_id}").joinpath(knowledge_base_id)
    if mode == "update":
        previous_docs = await _get_previous_doc_refs(
            event_store=event_store,
            knowledge_base_id=knowledge_base_id,
            docs_prompts=docs_prompts,
        )
        seed_previous_auto_docs(
            knowledge_repo=knowledge_repo,
            target_path=generated_docs_path,
            seeds=previous_docs,
        )
    await docs_agent.generate_documentation(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        knowledge_base_id=knowledge_base_id,
        output_path=generated_docs_path,
        docs_prompts=docs_prompts,
        process_id=process_id,
    )

    generated_documents: list[str] = []
    for doc_file in generated_docs_path.rglob("*"):
        if doc_file.is_file() and doc_file.suffix == ".md":
            relative_path = doc_file.relative_to(generated_docs_path)
            with doc_file.open("r") as f:
                content = f.read()
            knowledge_repo.add(
                KnowledgeBase(knowledge_base_id, code_version),
                str(relative_path),
                content,
                metadata={"origin": "auto", "process_id": process_id},
            )
            generated_documents.append(str(relative_path))

    return generated_documents


def seed_previous_auto_docs(
    *,
    knowledge_repo: KnowledgeRepository,
    target_path: Path,
    seeds: set[DocRef],
) -> None:
    if not seeds:
        return
    target_path.mkdir(parents=True, exist_ok=True)
    for ref in seeds:
        if not knowledge_repo.contains(ref.base, ref.document_name):
            continue
        if knowledge_repo.get_origin(ref.base, ref.document_name) != "auto":
            continue
        content = knowledge_repo.get_content(ref.base, ref.document_name)
        destination = target_path.joinpath(ref.document_name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)


async def _get_previous_doc_refs(
    *,
    event_store,
    knowledge_base_id: str,
    docs_prompts: dict[str, str],
) -> set[DocRef]:
    prompt_id, prompt_description = next(iter(docs_prompts.items()))
    setup = await load_auto_documentation_setup(event_store, knowledge_base_id)
    if not setup.prompt_matches(prompt_id, prompt_description):
        return set()
    previous_version = await _previous_version(
        event_store=event_store,
        knowledge_base_id=knowledge_base_id,
        prompt_id=prompt_id,
    )
    if not previous_version:
        return set()
    target_docs = {
        name if name.endswith(".md") else f"{name}.md" for name in docs_prompts.keys()
    }
    return {
        DocRef(KnowledgeBase(knowledge_base_id, previous_version), doc_name)
        for doc_name in target_docs
    }


async def _previous_version(
    *, event_store, knowledge_base_id: str, prompt_id: str
) -> str | None:
    completions = await event_store.find(
        {"knowledge_base_id": knowledge_base_id, "prompt_id": prompt_id},
        DocumentationGenerationCompleted,
    )
    if not completions:
        return None
    latest_generated_doc = max(completions, key=lambda e: e.occurred_at)
    return latest_generated_doc.code_version if latest_generated_doc else None


def load_existing_markdown_documents(
    *,
    repo_path: Path,
    knowledge_repo: KnowledgeRepository,
    knowledge_base_id: str,
    code_version: str,
    process_id: str,
) -> None:
    if not repo_path.exists():
        return

    kb_key = KnowledgeBase(knowledge_base_id, code_version)
    for doc_file in repo_path.rglob("*.md"):
        if not doc_file.is_file():
            continue
        try:
            content = doc_file.read_text()
        except OSError:
            continue
        relative_path = doc_file.relative_to(repo_path)
        knowledge_repo.add(
            kb_key,
            str(relative_path),
            content,
            metadata={"origin": "repo", "process_id": process_id},
        )
