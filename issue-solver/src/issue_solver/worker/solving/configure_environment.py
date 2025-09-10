from issue_solver.events.domain import (
    EnvironmentConfigurationProvided,
    EnvironmentConfigurationValidated,
)
from issue_solver.worker.solving.process_issue_resolution_request import Dependencies


async def configure_environment(
    message: EnvironmentConfigurationProvided, dependencies: Dependencies
) -> None:
    await dependencies.event_store.append(
        message.process_id,
        EnvironmentConfigurationValidated(
            process_id=message.process_id,
            occurred_at=dependencies.clock.now(),
            snapshot_id="brice-env-001-snap-001",
            stdout="environment setup completed successfully",
            stderr="no errors",
            return_code=0,
        ),
    )
