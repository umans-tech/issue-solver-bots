import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from issue_solver.clock import Clock
from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryTokenRotated,
    CodeRepositoryIndexed,
    DocumentationPromptsDefined,
    DocumentationPromptsRemoved,
    RepositoryIndexationRequested,
    EnvironmentConfigurationProvided,
)
from issue_solver.events.event_store import EventStore
from issue_solver.git_operations.git_helper import (
    GitValidationError,
    GitValidationService,
)
from issue_solver.webapi.dependencies import (
    get_clock,
    get_event_store,
    get_logger,
    get_validation_service,
    get_user_id_or_default,
)
from issue_solver.webapi.payloads import (
    ConnectRepositoryRequest,
    RotateTokenRequest,
    EnvironmentConfiguration,
    AutoDocumentationConfigRequest,
    AutoDocumentationDeleteRequest,
    AutoDocManualGenerationRequest,
)
from issue_solver.events.auto_documentation import (
    load_auto_documentation_setup,
    CannotRemoveAutoDocumentationWithoutPrompts,
    CannotRemoveUnknownAutoDocumentationPrompts,
)
from issue_solver.events.domain import (
    DocumentationGenerationRequested,
)
from issue_solver.worker.logging_config import logger as worker_logger
from openai import OpenAI

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/", status_code=201)
async def connect_repository(
    connect_repository_request: ConnectRepositoryRequest,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.repository.connect")),
    ],
    clock: Annotated[Clock, Depends(get_clock)],
    validation_service: Annotated[
        GitValidationService, Depends(get_validation_service)
    ],
) -> dict[str, str]:
    """Connect to a code repository."""
    validation_result = _validate_repository_access(
        connect_repository_request, logger, validation_service
    )

    process_id = str(uuid.uuid4())
    logger.info(f"Creating new repository connection with process ID: {process_id}")

    client = OpenAI()
    repo_name = connect_repository_request.url.split("/")[-1]
    logger.info(f"Creating vector store for repository: {repo_name}")

    # Convert token permissions to JSON serializable dict
    access_token_permissions = None
    if validation_result and validation_result.token_permissions:
        tp = validation_result.token_permissions
        access_token_permissions = {
            "scopes": tp.scopes,
            "has_repo": tp.has_repo,
            "has_workflow": tp.has_workflow,
            "has_read_user": tp.has_read_user,
            "missing_scopes": tp.missing_scopes,
            "is_optimal": tp.is_optimal,
        }

    vector_store = client.vector_stores.create(name=repo_name)
    event = CodeRepositoryConnected(
        occurred_at=clock.now(),
        url=connect_repository_request.url,
        access_token=connect_repository_request.access_token,
        user_id=user_id,
        space_id=connect_repository_request.space_id,
        knowledge_base_id=vector_store.id,
        process_id=process_id,
        token_permissions=access_token_permissions,
    )
    await event_store.append(process_id, event)

    logger.info(
        f"Repository connection created successfully with process ID: {process_id}"
    )
    return {
        "url": event.url,
        "process_id": event.process_id,
        "knowledge_base_id": event.knowledge_base_id,
    }


@router.post("/{knowledge_base_id}", status_code=200)
async def index_new_changes(
    knowledge_base_id: str,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.repository.index")),
    ],
    clock: Annotated[Clock, Depends(get_clock)],
) -> dict[str, str]:
    """Index new changes in the code repository."""
    logger.info(f"Indexing new changes for knowledge base ID: {knowledge_base_id}")

    # Find the repository connection with the given knowledge_base_id
    repository_connections = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, CodeRepositoryConnected
    )

    # Check if any repository was found
    if not repository_connections:
        logger.error(f"No repository found with knowledge base ID: {knowledge_base_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No repository found with knowledge base ID: {knowledge_base_id}",
        )

    event = RepositoryIndexationRequested(
        occurred_at=clock.now(),
        knowledge_base_id=knowledge_base_id,
        process_id=repository_connections[0].process_id,
        user_id=user_id,
    )
    await event_store.append(event.process_id, event)
    logger.info(
        f"New changes indexed successfully for knowledge base ID: {knowledge_base_id}"
    )
    return {"message": "New changes indexed successfully"}


@router.put("/{knowledge_base_id}/token", status_code=200)
async def rotate_token(
    knowledge_base_id: str,
    rotate_token_request: RotateTokenRequest,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(
            lambda: get_logger("issue_solver.webapi.routers.repository.rotate_token")
        ),
    ],
    clock: Annotated[Clock, Depends(get_clock)],
    validation_service: Annotated[
        GitValidationService, Depends(get_validation_service)
    ],
) -> dict[str, Any]:
    """Rotate the access token for a connected repository."""
    logger.info(f"Rotating token for knowledge base ID: {knowledge_base_id}")

    # Find the repository connection with the given knowledge_base_id
    repository_connections = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, CodeRepositoryConnected
    )

    if not repository_connections:
        logger.error(f"No repository found with knowledge base ID: {knowledge_base_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No repository found with knowledge base ID: {knowledge_base_id}",
        )

    repository_connection = repository_connections[0]

    try:
        validation_result = validation_service.validate_repository_access(
            repository_connection.url, rotate_token_request.access_token
        )
    except GitValidationError as e:
        logger.error(f"Token validation failed: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)

    token_permissions = None
    if validation_result and validation_result.token_permissions:
        token_permissions = validation_result.token_permissions.to_dict()

    event = CodeRepositoryTokenRotated(
        occurred_at=clock.now(),
        knowledge_base_id=knowledge_base_id,
        new_access_token=rotate_token_request.access_token,
        user_id=user_id,
        process_id=repository_connection.process_id,
        token_permissions=token_permissions,
    )
    await event_store.append(repository_connection.process_id, event)

    logger.info(
        f"Token rotated successfully for knowledge base ID: {knowledge_base_id}"
    )
    return {
        "message": "Token rotated successfully",
        "token_permissions": token_permissions,
    }


@router.post(
    "/{knowledge_base_id}/environments",
    status_code=201,
)
async def create_environment(
    knowledge_base_id: str,
    environment_config: EnvironmentConfiguration,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(
            lambda: get_logger(
                "issue_solver.webapi.routers.repository.create_environment"
            )
        ),
    ],
):
    """Configure a development environment for the knowledge base / repository.
    Coding agents could use this environment to resolve issues in this code repository.
    """
    logger.info(f"Creating environment for knowledge base ID: {knowledge_base_id}")

    repository_connections = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, CodeRepositoryConnected
    )

    if not repository_connections:
        logger.error(f"No repository found with knowledge base ID: {knowledge_base_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No repository found with knowledge base ID: {knowledge_base_id}",
        )

    environment_id = str(uuid.uuid4())
    event = EnvironmentConfigurationProvided(
        environment_id=environment_id,
        occurred_at=clock.now(),
        process_id=str(uuid.uuid4()),
        knowledge_base_id=knowledge_base_id,
        global_setup=environment_config.global_setup,
        project_setup=environment_config.project_setup,
        user_id=user_id,
    )

    await event_store.append(event.process_id, event)
    logger.info(f"Environment created with data: {environment_config}")

    return {
        "environment_id": environment_id,
        "process_id": event.process_id,
    }


@router.post(
    "/{knowledge_base_id}/auto-documentation",
    status_code=201,
)
async def configure_auto_documentation(
    knowledge_base_id: str,
    auto_doc_config: AutoDocumentationConfigRequest,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(
            lambda: get_logger(
                "issue_solver.webapi.routers.repository.configure_auto_documentation"
            )
        ),
    ],
):
    """Define prompts that enable automatic documentation generation."""

    logger.info(
        "Configuring automatic documentation for knowledge base ID: %s",
        knowledge_base_id,
    )

    await _ensure_repository_connection_or_404(
        knowledge_base_id=knowledge_base_id,
        event_store=event_store,
        logger=logger,
    )

    auto_doc_setup = await load_auto_documentation_setup(
        event_store=event_store, knowledge_base_id=knowledge_base_id
    )

    process_id = auto_doc_setup.last_process_id or str(uuid.uuid4())
    event = DocumentationPromptsDefined(
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        docs_prompts=auto_doc_config.docs_prompts,
        process_id=process_id,
        occurred_at=clock.now(),
    )
    await event_store.append(process_id, event)

    updated_setup = auto_doc_setup.apply(event)

    logger.info(
        "Automatic documentation configured for knowledge base ID: %s with process ID: %s",
        knowledge_base_id,
        process_id,
    )

    return {
        "process_id": process_id,
        "knowledge_base_id": knowledge_base_id,
        "docs_prompts": updated_setup.docs_prompts,
    }


@router.delete(
    "/{knowledge_base_id}/auto-documentation",
    status_code=200,
)
async def remove_auto_documentation_prompts(
    knowledge_base_id: str,
    delete_request: AutoDocumentationDeleteRequest,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(
            lambda: get_logger(
                "issue_solver.webapi.routers.repository.remove_auto_documentation"
            )
        ),
    ],
):
    """Remove documentation prompts for a repository."""

    logger.info(
        "Removing %d auto documentation prompts for knowledge base ID: %s",
        len(delete_request.prompt_ids),
        knowledge_base_id,
    )

    await _ensure_repository_connection_or_404(
        knowledge_base_id=knowledge_base_id,
        event_store=event_store,
        logger=logger,
    )

    auto_doc_setup = await load_auto_documentation_setup(
        event_store=event_store, knowledge_base_id=knowledge_base_id
    )

    process_id = auto_doc_setup.last_process_id or str(uuid.uuid4())
    event = DocumentationPromptsRemoved(
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        prompt_ids=delete_request.prompt_ids,
        process_id=process_id,
        occurred_at=clock.now(),
    )

    try:
        updated_setup = auto_doc_setup.apply(event)
    except CannotRemoveAutoDocumentationWithoutPrompts as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CannotRemoveUnknownAutoDocumentationPrompts as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await event_store.append(process_id, event)

    return {
        "process_id": process_id,
        "knowledge_base_id": knowledge_base_id,
        "deleted_prompt_ids": delete_request.prompt_ids,
        "docs_prompts": updated_setup.docs_prompts,
    }


@router.get(
    "/{knowledge_base_id}/auto-documentation",
    status_code=200,
)
async def get_auto_documentation(
    knowledge_base_id: str,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(
            lambda: get_logger(
                "issue_solver.webapi.routers.repository.get_auto_documentation"
            )
        ),
    ],
):
    """Retrieve the latest auto-documentation prompt configuration for a repository."""

    repository_connection = await _ensure_repository_connection_or_404(
        knowledge_base_id=knowledge_base_id,
        event_store=event_store,
        logger=logger,
    )
    logger.info(
        "Fetching automatic documentation prompts for knowledge base ID: %s",
        knowledge_base_id,
    )

    auto_doc_setup = await load_auto_documentation_setup(
        event_store=event_store,
        knowledge_base_id=repository_connection.knowledge_base_id,
    )

    return {
        "knowledge_base_id": knowledge_base_id,
        "docs_prompts": auto_doc_setup.docs_prompts,
        "updated_at": auto_doc_setup.updated_at.isoformat()
        if auto_doc_setup.updated_at
        else None,
        "last_process_id": auto_doc_setup.last_process_id,
    }


@router.post(
    "/{knowledge_base_id}/auto-documentation/generate",
    status_code=201,
)
async def trigger_auto_document_generation(
    knowledge_base_id: str,
    request: AutoDocManualGenerationRequest,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
):
    """Trigger on-demand auto documentation generation for a specific prompt."""
    setup = await load_auto_documentation_setup(event_store, knowledge_base_id)
    prompt_description = setup.docs_prompts.get(request.prompt_id)
    if not prompt_description:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt {request.prompt_id} not found for knowledge base {knowledge_base_id}",
        )

    latest_commit = await _latest_indexed_commit(event_store, knowledge_base_id)
    if not latest_commit:
        raise HTTPException(
            status_code=409,
            detail="Repository has not been indexed yet; cannot generate documentation.",
        )

    process_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    event = DocumentationGenerationRequested(
        knowledge_base_id=knowledge_base_id,
        prompt_id=request.prompt_id,
        prompt_description=prompt_description,
        code_version=latest_commit,
        run_id=run_id,
        process_id=process_id,
        occurred_at=clock.now(),
        mode=request.mode,  # type: ignore[arg-type]
    )
    await event_store.append(process_id, event)
    worker_logger.info(
        "Auto-doc manual generation requested",
        extra={
            "knowledge_base_id": knowledge_base_id,
            "prompt_id": request.prompt_id,
            "mode": request.mode,
            "code_version": latest_commit,
            "process_id": process_id,
            "run_id": run_id,
            "user_id": user_id,
        },
    )
    return {"process_id": process_id, "run_id": run_id}


@router.get(
    "/{knowledge_base_id}/environments/latest",
)
async def get_latest_environment(
    knowledge_base_id: str,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(
            lambda: get_logger(
                "issue_solver.webapi.routers.repository.get_latest_environment"
            )
        ),
    ],
):
    """Return the most recent environment configuration for the repository if any."""
    logger.info(
        f"Retrieving latest environment for knowledge base ID: {knowledge_base_id}"
    )

    events = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, EnvironmentConfigurationProvided
    )

    if not events:
        raise HTTPException(status_code=404, detail="No environment found")

    # Pick most recent by occurred_at
    latest = max(events, key=lambda e: e.occurred_at)
    return {
        "environment_id": latest.environment_id,
        "process_id": latest.process_id,
        "occurred_at": latest.occurred_at.isoformat(),
        "global": latest.global_setup,
        "project": latest.project_setup,
    }


async def _ensure_repository_connection_or_404(
    *,
    knowledge_base_id: str,
    event_store: EventStore,
    logger: logging.Logger | logging.LoggerAdapter,
) -> CodeRepositoryConnected:
    repository_connections = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, CodeRepositoryConnected
    )

    if not repository_connections:
        logger.error(
            "No repository found with knowledge base ID: %s",
            knowledge_base_id,
        )
        raise HTTPException(
            status_code=404,
            detail=f"No repository found with knowledge base ID: {knowledge_base_id}",
        )
    return repository_connections[0]


def _validate_repository_access(connect_repository_request, logger, validation_service):
    try:
        validation_result = validation_service.validate_repository_access(
            connect_repository_request.url, connect_repository_request.access_token
        )
        return validation_result
    except GitValidationError as e:
        logger.error(f"Repository validation failed: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)


async def _latest_indexed_commit(
    event_store: EventStore, knowledge_base_id: str
) -> str | None:
    indexed_events = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, CodeRepositoryIndexed
    )
    if not indexed_events:
        return None
    latest = max(indexed_events, key=lambda e: e.occurred_at)
    return latest.commit_sha
