import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from issue_solver.events.in_memory_event_store import InMemoryEventStore
from issue_solver.webapi.routers import resolutions, repository, processes

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Get logger for your module
logger = logging.getLogger("issue_solver.webapi")
logger.setLevel(logging.INFO)

# Make sure it propagates up to root logger
logger.propagate = True


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Initialize and cleanup resources during application lifecycle."""
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
async def root():
    """Root endpoint that returns basic API information."""
    return {
        "name": "Issue Solver API",
        "version": "0.1.0",
        "status": "online",
    }
