import shutil
from pathlib import Path

from issue_solver.agents.issue_resolving_agent import DocumentingAgent
from issue_solver.events.code_repo_integration import fetch_repo_credentials
from issue_solver.events.domain import (
    CodeRepositoryIndexed,
    DocumentationPromptsDefined,
)
from issue_solver.events.event_store import EventStore
from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeBase,
    KnowledgeRepository,
)
from issue_solver.worker.dependencies import Dependencies


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
    )
    docs_prompts = await get_prompts_for_doc_to_generate(
        dependencies.event_store, event.knowledge_base_id
    )
    if docs_prompts:
        await generate_and_load_docs(
            docs_agent,
            dependencies.knowledge_repository,
            process_id,
            event.knowledge_base_id,
            code_version,
            docs_prompts,
        )


async def prepare_repo_path(process_id: str) -> Path:
    repo_path = Path(f"/tmp/repo/{process_id}")
    if repo_path.exists():
        shutil.rmtree(repo_path)
    return repo_path


async def get_prompts_for_doc_to_generate(
    event_store: EventStore, knowledge_base_id: str
) -> dict[str, str]:
    doc_prompts_defined_events = await event_store.find(
        {"knowledge_base_id": knowledge_base_id},
        DocumentationPromptsDefined,
    )
    documentation_prompts: dict[str, str] = {}
    for event in doc_prompts_defined_events:
        documentation_prompts.update(event.docs_prompts)

    return {
        key: value
        for key, value in documentation_prompts.items()
        if isinstance(value, str) and value.strip()
    }


async def generate_and_load_docs(
    docs_agent: DocumentingAgent,
    knowledge_repo: KnowledgeRepository,
    process_id: str,
    knowledge_base_id: str,
    code_version: str,
    docs_prompts: dict[str, str],
) -> None:
    generated_docs_path = Path(f"/tmp/repo/{process_id}").joinpath(knowledge_base_id)
    await docs_agent.generate_documentation(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        knowledge_base_id=knowledge_base_id,
        output_path=generated_docs_path,
        docs_prompts=docs_prompts,
        process_id=process_id,
    )

    for doc_file in generated_docs_path.rglob("*"):
        if doc_file.is_file() and doc_file.suffix == ".md":
            relative_path = doc_file.relative_to(generated_docs_path)
            with doc_file.open("r") as f:
                content = f.read()
            knowledge_repo.add(
                KnowledgeBase(knowledge_base_id, code_version),
                str(relative_path),
                content,
            )


def load_existing_markdown_documents(
    *,
    repo_path: Path,
    knowledge_repo: KnowledgeRepository,
    knowledge_base_id: str,
    code_version: str,
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
        knowledge_repo.add(kb_key, str(relative_path), content)
