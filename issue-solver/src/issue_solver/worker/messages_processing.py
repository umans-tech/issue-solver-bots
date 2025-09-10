from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    IssueResolutionRequested,
    EnvironmentConfigurationProvided,
)
from issue_solver.worker.indexing.delta import index_new_changes_codebase
from issue_solver.worker.indexing.full import index_codebase
from issue_solver.worker.logging_config import logger
from issue_solver.worker.solving.configure_environment import configure_environment
from issue_solver.worker.solving.process_issue_resolution_request import (
    Dependencies,
    resolve_issue,
)


async def process_event_message(
    message: AnyDomainEvent, dependencies: Dependencies
) -> None:
    try:
        match message:
            case CodeRepositoryConnected():
                await index_codebase(message)
            case CodeRepositoryIndexed():
                logger.info("Skipping already processed repository")
            case RepositoryIndexationRequested():
                await index_new_changes_codebase(message)
            case EnvironmentConfigurationProvided():
                logger.info("Skipping already processed environment")
                await configure_environment(message, dependencies)
            case IssueResolutionRequested():
                await resolve_issue(message, dependencies)
    except Exception as e:
        logger.error(f"Error processing repository message: {str(e)}")
        raise
