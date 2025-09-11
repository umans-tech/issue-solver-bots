import os
from pathlib import Path

from morphcloud.api import MorphCloudClient, Snapshot

from issue_solver.env_setup.dev_environments_management import (
    VMConfiguration,
    get_snapshot,
)

CURRENT_PATH = Path(os.path.abspath(os.path.dirname(__file__)))
DEFAULT_VCPUS = 8
DEFAULT_MEMORY = 8192  # 4GB
DEFAULT_DISK_SIZE = 16 * 1024  # 16GB in MB


def main():
    client = MorphCloudClient()
    vm_configuration = VMConfiguration(
        vcpus=DEFAULT_VCPUS, memory=DEFAULT_MEMORY, disk_size=DEFAULT_DISK_SIZE
    )
    script_path = CURRENT_PATH.joinpath("setup_cudu_cli_on_debian.sh").resolve()
    with open(script_path, "r") as file:
        install_cudu_script = file.read()
    base_snapshot = create_or_replace_base_cudu_snapshot(
        client, install_cudu_script, vm_configuration
    )
    print(f"Snapshot ready: {base_snapshot.id}  📸✅")


def create_or_replace_base_cudu_snapshot(
    client: MorphCloudClient,
    install_cudu_script: str,
    vm_configuration: VMConfiguration,
) -> Snapshot:
    existing_base_snapshot = get_snapshot(
        client,
        metadata={"type": "base"},
    )
    new_base_snapshot = create_new_base_snapshot(
        client, install_cudu_script, vm_configuration
    )
    if existing_base_snapshot:
        existing_base_snapshot.set_metadata({"type": "old_base"})
    return new_base_snapshot


def create_new_base_snapshot(
    client: MorphCloudClient,
    install_cudu_script: str,
    vm_configuration: VMConfiguration,
) -> Snapshot:
    tmp_snapshot = client.snapshots.create(
        vcpus=vm_configuration.vcpus,
        memory=vm_configuration.memory,
        disk_size=vm_configuration.disk_size,
        metadata={
            "type": "tmp",
        },
    )
    try:
        base_snapshot = tmp_snapshot.setup(
            command=install_cudu_script,
        )
        base_snapshot.set_metadata({"type": "base"})
        return base_snapshot
    finally:
        tmp_snapshot.delete()


if __name__ == "__main__":
    main()
