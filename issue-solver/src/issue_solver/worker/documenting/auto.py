from pathlib import Path

from issue_solver.agents.docs_prompts import suggested_docs_prompts
from issue_solver.events.code_repo_integration import fetch_repo_credentials
from issue_solver.events.domain import CodeRepositoryIndexed
from issue_solver.worker.documenting.knowledge_repository import KnowledgeBase
from issue_solver.worker.dependencies import Dependencies


async def generate_docs(
    message: CodeRepositoryIndexed, dependencies: Dependencies
) -> None:
    if not dependencies.docs_agent:
        raise RuntimeError("Docs agent is not configured")
    repo_credentials = await fetch_repo_credentials(
        event_store=dependencies.event_store,
        knowledge_base_id=message.knowledge_base_id,
    )
    process_id = dependencies.id_generator.new()
    dependencies.git_client.clone_repository(
        url=repo_credentials.url,
        access_token=repo_credentials.access_token,
        to_path=Path(f"/tmp/repo/{process_id}"),
    )
    generated_docs_path = Path(f"/tmp/repo/{process_id}").joinpath(
        message.knowledge_base_id
    )
    await dependencies.docs_agent.generate_documentation(
        repo_path=Path(f"/tmp/repo/{process_id}"),
        knowledge_base_id=message.knowledge_base_id,
        output_path=generated_docs_path,
        docs_prompts=suggested_docs_prompts(),
        process_id=process_id,
    )

    for doc_file in generated_docs_path.rglob("*"):
        if doc_file.is_file() and doc_file.suffix == ".md":
            relative_path = doc_file.relative_to(generated_docs_path)
            with doc_file.open("r") as f:
                content = f.read()
            dependencies.knowledge_repository.add(
                KnowledgeBase(message.knowledge_base_id, message.commit_sha),
                str(relative_path),
                content,
            )
