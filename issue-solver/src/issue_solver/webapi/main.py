import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from issue_solver.webapi.dependencies import (
    get_logger,
    init_webapi_event_store,
    init_agent_message_store,
)
from issue_solver.webapi.routers import (
    processes,
    repository,
    resolutions,
    mcp_repositories_proxy,
    webhooks,
)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Initialize and cleanup resources during application lifecycle."""
    # Get the logger directly using the dependency function
    logger = get_logger("issue_solver.webapi.lifespan")

    # Initialize the event store
    fastapi_app.state.event_store = await init_webapi_event_store()
    fastapi_app.state.agent_message_store = await init_agent_message_store()
    logger.info("Application started, event store initialized")
    yield
    # Cleanup
    del fastapi_app.state.event_store
    del fastapi_app.state.agent_message_store
    logger.info("Application shutdown, event store cleaned up")


app = FastAPI(
    title="Issue Solver API",
    description="API for solving issues in code repositories",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(resolutions.router)
app.include_router(repository.router)
app.include_router(processes.router)
app.include_router(mcp_repositories_proxy.router)
app.include_router(webhooks.router)


@app.get("/")
async def root(
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.root")),
    ],
):
    """Root endpoint that returns basic API information."""
    logger.info("Root endpoint accessed")
    return {
        "name": "Issue Solver API",
        "version": "0.1.0",
        "status": "online",
    }
