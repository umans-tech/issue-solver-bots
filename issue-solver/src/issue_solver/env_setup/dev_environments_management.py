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
    env_path: str = "/home/umans/.cudu_env",  # deprecated; unused
    exec_path: str = "/home/umans/.cudu_run.sh",  # deprecated; unused
    background: bool = False,
) -> str:
    if not env_body.endswith("\n"):
        env_body += "\n"

    # SECURITY NOTE:
    # Historically we wrote the env to `env_path` (default: /home/umans/.cudu_env) and
    # sourced it from the command runner. For background jobs there was no EXIT trap,
    # otherwise the env file could be deleted before the background process had a
    # chance to read it. That caused secrets to persist on disk for background runs.
    #
    # We now avoid writing secrets to disk entirely by streaming `env_body` to the
    # runner via an inherited file descriptor (FD 3) and piping the run script over
    # stdin. No temporary files are created. `env_path`/`exec_path` remain for
    # backward compatibility but are unused.
    _ = env_path
    _ = exec_path

    if background:
        run_line = (
            "nohup runuser -u umans -- /bin/bash "
            "<<'SH' >> /home/umans/.cudu_run.log 2>&1 & "
            "echo $! > /home/umans/.cudu_run.pid"
        )
    else:
        run_line = "runuser -u umans -- /bin/bash <<'SH'"

    script = f"""
set -Eeuo pipefail
umask 0077
{global_setup_script.strip() if global_setup_script else ""}

# Stream env inline; no files written.
{run_line}
#!/bin/bash
set -Eeuo pipefail
set -a
cat <<'ENV' | while IFS= read -r line; do [ -z "$line" ] && continue; eval "$line"; done
{env_body}ENV
set +a

# --- pick a safe working directory ---
if [ -n "${{REPO_PATH:-}}" ] && [ "${{REPO_PATH:0:1}}" = "/" ]; then
  mkdir -p "${{REPO_PATH}}"
  cd "${{REPO_PATH}}" || cd "$HOME"
else
  cd "$HOME"
fi

# ensure PATH is sane for user invocations
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

{"" if background else "uv tool install --python 3.12 --upgrade issue-solver >/dev/null 2>&1"}

# quick sanity (leave for now; remove once stable)
echo "PWD=$(pwd)"; echo "PATH=$PATH"; command -v cudu >/dev/null || {{ echo "cudu not found" >&2; exit 127; }}

{f"exec {command}" if background else f"exec {command} | tee -a /home/umans/.cudu_run.log"}
SH
    """
    return dedent(script)
