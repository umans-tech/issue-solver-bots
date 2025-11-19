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
)
from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeBase,
    KnowledgeRepository,
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
    process_id = dependencies.id_generator.new()
    repo_path = await prepare_repo_path(process_id)
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

    parent_process_id = auto_doc_setup.last_process_id or event.process_id
    for prompt_id, prompt_description in auto_doc_setup.docs_prompts.items():
        child_process_id = dependencies.id_generator.new()
        await dependencies.event_store.append(
            child_process_id,
            DocumentationGenerationRequested(
                knowledge_base_id=event.knowledge_base_id,
                prompt_id=prompt_id,
                prompt_description=prompt_description,
                code_version=code_version,
                parent_process_id=parent_process_id,
                process_id=child_process_id,
                occurred_at=dependencies.clock.now(),
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
            parent_process_id=event.parent_process_id,
            process_id=event.process_id,
            occurred_at=dependencies.clock.now(),
        ),
    )

    try:
        generated_docs = await generate_and_load_docs(
            docs_agent,
            dependencies.knowledge_repository,
            event.process_id,
            event.knowledge_base_id,
            event.code_version,
            {event.prompt_id: event.prompt_description},
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
                parent_process_id=event.parent_process_id,
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
            parent_process_id=event.parent_process_id,
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
    process_id: str,
    knowledge_base_id: str,
    code_version: str,
    docs_prompts: dict[str, str],
) -> list[str]:
    generated_docs_path = Path(f"/tmp/repo/{process_id}").joinpath(knowledge_base_id)
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
