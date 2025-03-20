import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends

from issue_solver.events.in_memory_event_store import InMemoryEventStore
from issue_solver.webapi.dependencies import get_logger
from issue_solver.webapi.routers import resolutions, repository, processes


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Initialize and cleanup resources during application lifecycle."""
    # Get the logger directly using the dependency function
    logger = get_logger("issue_solver.webapi.lifespan")

    # Initialize the event store
    fastapi_app.state.event_store = InMemoryEventStore()
    logger.info("Application started, in-memory event store initialized")
    yield
    # Cleanup
    del fastapi_app.state.event_store
    logger.info("Application shutdown, in-memory event store cleaned up")


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
