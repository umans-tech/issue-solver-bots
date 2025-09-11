from morphcloud.api import MorphCloudClient

import argparse
from issue_solver.env_setup.dev_environments_management import (
    VMConfiguration,
    get_or_create_snapshot_dev_snapshot,
)

DEFAULT_VCPUS = 4
DEFAULT_MEMORY = 4096  # 4GB
DEFAULT_DISK_SIZE = 8192  # 8GB


def main():
    client = MorphCloudClient()

    parser = argparse.ArgumentParser(
        description="Create or retrieve a development snapshot."
    )
    parser.add_argument(
        "--deps",
        type=str,
        nargs="+",
        help="List of dependencies to install (e.g., python, git)",
    )
    parser.add_argument(
        "--commands",
        type=str,
        action="append",
        help="Command to run after dependencies are installed (can be specified multiple times, e.g., --commands='pip install pytest' --commands='black --check .')",
    )
    parser.add_argument(
        "--knowledge-base-id",
        type=str,
        default="vs-knowledge-base-id-1234567893",
        help="Knowledge base ID (default: vs-knowledge-base-id-1234567893)",
    )
    args = parser.parse_args()

    # Process dependencies
    dependencies = []
    if args.deps:
        for dep in args.deps:
            # Clean up malformed arguments (remove --deps= prefix if present)
            cleaned_dep = dep.replace("--deps=", "").strip()
            # Split by comma if multiple dependencies in one string
            if "," in cleaned_dep:
                dependencies.extend([d.strip() for d in cleaned_dep.split(",")])
            else:
                dependencies.append(cleaned_dep)

    # Process commands
    commands = []
    if args.commands:
        for cmd in args.commands:
            # Clean up malformed arguments (remove --commands= prefix if present)
            cleaned_cmd = cmd.replace("--commands=", "").strip()
            # Remove quotes if they're part of the string
            if cleaned_cmd.startswith('"') and cleaned_cmd.endswith('"'):
                cleaned_cmd = cleaned_cmd[1:-1]
            commands.append(cleaned_cmd)

    print(f"- dependencies={dependencies}")
    print(f"- commands={commands}")

    knowledge_base_id = args.knowledge_base_id
    print(f"- knowledge_base_id={knowledge_base_id}")

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
