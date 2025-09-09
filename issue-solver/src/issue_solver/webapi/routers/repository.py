import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from issue_solver.clock import Clock
from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryTokenRotated,
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
)
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


def _validate_repository_access(connect_repository_request, logger, validation_service):
    try:
        validation_result = validation_service.validate_repository_access(
            connect_repository_request.url, connect_repository_request.access_token
        )
        return validation_result
    except GitValidationError as e:
        logger.error(f"Repository validation failed: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
