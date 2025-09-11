from pathlib import Path

from morphcloud.api import Snapshot, MorphCloudClient

from issue_solver.cli.prepare_command import PrepareCommandSettings
from issue_solver.dev_environments_management import run_as_umans_with_env
from issue_solver.events.code_repo_integration import (
    fetch_repo_credentials,
)
from issue_solver.events.domain import (
    EnvironmentConfigurationProvided,
    EnvironmentConfigurationValidated,
)
from issue_solver.git_operations.git_helper import (
    extract_git_clone_default_directory_name,
)
from issue_solver.worker.solving.process_issue_resolution_request import Dependencies


async def configure_environment(
    message: EnvironmentConfigurationProvided, dependencies: Dependencies
) -> None:
    base_snapshot = get_base_snapshot(dependencies.microvm_client)
    knowledge_base_id = message.knowledge_base_id
    repo_credentials = await fetch_repo_credentials(
        dependencies.event_store, knowledge_base_id
    )
    process_id = message.process_id
    default_clone_path = Path(
        extract_git_clone_default_directory_name(repo_credentials.url)
    )
    prepare_command_env = PrepareCommandSettings(
        process_id=process_id,
        repo_path=default_clone_path,
        url=repo_credentials.url,
        access_token=repo_credentials.access_token,
        issue=None,
        install_script=message.project_setup,
    ).to_env_script()
    cmd = run_as_umans_with_env(
        prepare_command_env,
        "cudu prepare",
        message.global_setup,
    )
    snapshot = base_snapshot.exec(cmd)
    snapshot.set_metadata(
        {
            "type": "dev",
            "knowledge_base_id": knowledge_base_id,
            "environment_id": message.environment_id,
        }
    )
    await dependencies.event_store.append(
        process_id,
        EnvironmentConfigurationValidated(
            process_id=process_id,
            occurred_at=dependencies.clock.now(),
            snapshot_id=snapshot.id,
            stdout="environment setup completed successfully",
            stderr="no errors",
            return_code=0,
        ),
    )


def get_base_snapshot(microvm_client: MorphCloudClient | None) -> Snapshot:
    base_snapshots = (
        microvm_client.snapshots.list(
            metadata={
                "type": "base",
            }
        )
        if microvm_client
        else None
    )
    if not base_snapshots:
        raise RuntimeError("No base snapshot found for environment configuration")

    base_snapshot = base_snapshots[0]
    return base_snapshot
