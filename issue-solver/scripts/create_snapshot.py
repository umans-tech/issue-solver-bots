from morphcloud.api import MorphCloudClient

from issue_solver.dev_environments_management import (
    VMConfiguration,
    get_or_create_snapshot_dev_snapshot,
)

DEFAULT_VCPUS = 4
DEFAULT_MEMORY = 4096  # 4GB
DEFAULT_DISK_SIZE = 8192  # 8GB


def main():
    client = MorphCloudClient()

    knowledge_base_id = "vs-knowledge-base-id-1234567890"
    dependencies = [
        "docker",
    ]
    commands = [
        "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "curl -LsSf https://get.pnpm.io/install.sh | sh",
        "curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin",
        "uv python install",
    ]

    vm_configuration = VMConfiguration(
        vcpus=DEFAULT_VCPUS, memory=DEFAULT_MEMORY, disk_size=DEFAULT_DISK_SIZE
    )
    snapshot = get_or_create_snapshot_dev_snapshot(
        client,
        vm_configuration=vm_configuration,
        knowledge_base_id=knowledge_base_id,
        dependencies=dependencies,
        commands=commands,
    )

    if snapshot:
        print(f"Snapshot ready: {snapshot.id}")
    else:
        print("Failed to create or find a suitable snapshot.")


if __name__ == "__main__":
    main()
