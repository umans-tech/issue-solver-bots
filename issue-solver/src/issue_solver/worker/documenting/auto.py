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
    message: CodeRepositoryIndexed, dependencies: Dependencies
) -> None:
    docs_agent = dependencies.docs_agent
    if not docs_agent:
        raise RuntimeError("Docs agent is not configured")
    event_store = dependencies.event_store
    knowledge_base_id = message.knowledge_base_id
    repo_credentials = await fetch_repo_credentials(
        event_store=event_store,
        knowledge_base_id=knowledge_base_id,
    )
    process_id = dependencies.id_generator.new()
    dependencies.git_client.clone_repository(
        url=repo_credentials.url,
        access_token=repo_credentials.access_token,
        to_path=Path(f"/tmp/repo/{process_id}"),
    )
    docs_prompts = await get_prompts_for_doc_to_generate(event_store, knowledge_base_id)
    knowledge_repo = dependencies.knowledge_repository
    code_version = message.commit_sha
    if docs_prompts:
        await generate_and_load_docs(
            docs_agent,
            knowledge_repo,
            process_id,
            knowledge_base_id,
            code_version,
            docs_prompts,
        )


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
