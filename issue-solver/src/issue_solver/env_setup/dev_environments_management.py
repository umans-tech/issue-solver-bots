import sys
from dataclasses import dataclass
from enum import StrEnum
from textwrap import dedent
from typing import Any

from morphcloud.api import MorphCloudClient, Snapshot


@dataclass
class VMConfiguration:
    vcpus: int
    memory: int
    disk_size: int


class ExecutionEnvironmentPreference(StrEnum):
    NO_ENV_REQUIRED = "NO_ENV_REQUIRED"  # Can run in Lambda directly
    ENV_PREFERRED = "ENV_PREFERRED"  # Prefer MicroVM but fallback to Lambda
    ENV_REQUIRED = "ENV_REQUIRED"  # Must run in MicroVM, fail if unavailable


def run_ssh_command(instance, command, sudo=False, print_output=True):
    """Run a command on the instance via SSH and return the result"""
    if sudo and not command.startswith("sudo "):
        command = f"sudo {command}"

    print(f"Running on VM: {command}")
    result = instance.exec(command)

    if print_output:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"ERR: {result.stderr}", file=sys.stderr)

    if result.exit_code != 0:
        print(f"Command failed with exit code {result.exit_code}")

    return result


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
    dependencies_commands = [
        get_dependencies_as_one_installation_commands(dependencies)
    ]
    prepared_snapshot_for_dev_environment = base_snapshot
    for command in dependencies_commands + commands:
        command = command.strip()
        if command:
            print(f"Running command on base snapshot: {command}")
            prepared_snapshot_for_dev_environment = (
                prepared_snapshot_for_dev_environment.setup(command)
            )
    prepared_snapshot_for_dev_environment.set_metadata(snapshot_metadata)

    return prepared_snapshot_for_dev_environment


def get_or_create_base_snapshot(
    client: MorphCloudClient,
    vm_configuration: "VMConfiguration",
) -> Snapshot:
    snapshot_type = "base"
    existing_snapshot = get_snapshot(client, metadata={"type": snapshot_type})

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


def get_dependencies_as_one_installation_commands(dependencies: list[str]) -> str:
    dependencies_str = " ".join(dependencies)
    print(f"Dependencies to install: {dependencies_str}")
    return f"DEBIAN_FRONTEND=noninteractive apt update -q && DEBIAN_FRONTEND=noninteractive apt install -y -q {dependencies_str}"


def get_snapshot(client: MorphCloudClient, metadata: dict[str, Any]) -> Snapshot | None:
    snapshot_type = metadata.get("type", "unknown")
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


def run_as_umans_with_env(
    env_body: str,
    command: str,
    global_setup_script: str | None = None,
    env_path: str = "/home/umans/.cudu_env",
    exec_path: str = "/home/umans/.cudu_run.sh",
) -> str:
    if not env_body.endswith("\n"):
        env_body += "\n"

    script = f"""
set -Eeuo pipefail
umask 0077
{global_setup_script.strip() if global_setup_script else ""}
trap 'rm -f "{env_path}" "{exec_path}"' EXIT

# 1) write .env literally
cat > "{env_path}" <<'ENV'
{env_body}ENV
chown umans:umans "{env_path}"
chmod 600 "{env_path}"

# 2) write the exec script literally (owned by umans)
cat > "{exec_path}" <<'SH'
#!/bin/bash
set -Eeuo pipefail
set -a
. "{env_path}"
set +a

# --- pick a safe working directory so .env is readable ---
if [ -n "${{REPO_PATH:-}}" ] && [ "${{REPO_PATH:0:1}}" = "/" ]; then
  cd "${{REPO_PATH}}" || cd "$HOME"
else
  cd "$HOME"
fi

# ensure PATH is sane for user invocations
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# quick sanity (leave for now; remove once stable)
echo "PWD=$(pwd)"; echo "PATH=$PATH"; command -v cudu >/dev/null || {{ echo "cudu not found" >&2; exit 127; }}

exec {command} | tee -a /home/umans/.cudu_run.log
SH
chown umans:umans "{exec_path}"
chmod 700 "{exec_path}"

# 3) run as umans without -c or -l
runuser -u umans -- /bin/bash "{exec_path}"
"""
    return dedent(script)
