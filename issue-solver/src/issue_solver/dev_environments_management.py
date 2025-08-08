from dataclasses import dataclass
from typing import Any

from morphcloud.api import MorphCloudClient, Snapshot


@dataclass
class VMConfiguration:
    vcpus: int
    memory: int
    disk_size: int


def get_or_create_snapshot_dev_snapshot(
    client: MorphCloudClient,
    vm_configuration: "VMConfiguration",
    knowledge_base_id: str,
    dependencies: list[str],
    commands: list[str],
) -> Snapshot:
    """Get an existing snapshot with matching metadata or create a new one"""
    snapshot_type = "dev"
    existing_snapshot = get_snapshot(
        client,
        snapshot_type,
        metadata={"type": snapshot_type, "knowledge_base_id": knowledge_base_id},
    )
    snapshot_metadata = {
        "type": snapshot_type,
        "knowledge_base_id": knowledge_base_id,
    }
    snapshot = existing_snapshot or create_new_snapshot(
        client,
        vm_configuration,
        snapshot_metadata,
        dependencies,
        commands,
    )

    return snapshot


def replace_or_create_snapshot_dev_snapshot(
    client: MorphCloudClient,
    vm_configuration: "VMConfiguration",
    knowledge_base_id: str,
    dependencies: list[str],
    commands: list[str],
) -> Snapshot:
    """Get an existing snapshot with matching metadata or create a new one"""
    snapshot_type = "dev"
    existing_snapshot = get_snapshot(
        client,
        snapshot_type,
        metadata={"type": snapshot_type, "knowledge_base_id": knowledge_base_id},
    )
    snapshot_metadata = {
        "type": snapshot_type,
        "knowledge_base_id": knowledge_base_id,
    }
    snapshot = create_new_snapshot(
        client,
        vm_configuration,
        snapshot_metadata,
        dependencies,
        commands,
    )
    if existing_snapshot:
        print(f"Updating existing snapshot {existing_snapshot.id} with new commands...")
        existing_snapshot.delete()

    return snapshot


def create_new_snapshot(
    client: MorphCloudClient,
    vm_configuration: "VMConfiguration",
    snapshot_metadata: dict[str, Any],
    dependencies: list[str],
    commands: list[str],
) -> Snapshot:
    base_snapshot = get_or_create_base_snapshot(client, vm_configuration)

    print("Preparing Dev Snapshot...")
    instance = client.instances.start(base_snapshot.id)

    dependencies_commands = get_installation_commands(dependencies)
    for command in dependencies_commands + commands:
        print(f"Running command: {command}")
        instance_exec = instance.exec(command)
        print(f"Instance exec response: {instance_exec.model_dump()}")

    print("Creating Dev Snapshot...")
    prepared_snapshot_for_dev_environment = instance.snapshot(
        metadata=snapshot_metadata
    )
    instance.stop()

    return prepared_snapshot_for_dev_environment


def get_or_create_base_snapshot(
    client: MorphCloudClient,
    vm_configuration: "VMConfiguration",
) -> Snapshot:
    snapshot_type = "base"
    existing_snapshot = get_snapshot(
        client, snapshot_type, metadata={"type": snapshot_type}
    )

    base_snapshot_metadata = {"type": snapshot_type}
    snapshot = existing_snapshot or client.snapshots.create(
        vcpus=vm_configuration.vcpus,
        memory=vm_configuration.memory,
        disk_size=vm_configuration.disk_size,
        metadata=base_snapshot_metadata,
    )
    return snapshot


def get_installation_commands(dependencies):
    dependencies_commands = []
    for dependency in dependencies:
        print(f"Gathering dependency commands: {dependency}")
        dependencies_commands.append(
            f"DEBIAN_FRONTEND=noninteractive apt-get update -q && DEBIAN_FRONTEND=noninteractive apt-get install -y -q {dependency}"
        )
    return dependencies_commands


def get_snapshot(
    client: MorphCloudClient, snapshot_type: str, metadata: dict[str, Any]
) -> Snapshot | None:
    print(f"Looking for existing snapshot with type '{snapshot_type}'...")
    existing_snapshots = client.snapshots.list(metadata=metadata)
    for existing_snapshot in existing_snapshots:
        if existing_snapshot.status == "ready":
            print(
                f"Found existing snapshot {existing_snapshot.id} with type '{snapshot_type}'"
            )
            return existing_snapshot

    print(f"No existing snapshot found with type '{snapshot_type}'")
    return None
