import re
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
    EnvironmentValidationFailed,
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
    )
    if message.global_setup:
        try:
            base_snapshot = base_snapshot.exec(message.global_setup)
        except Exception as e:
            extras = [repo_credentials.url]
            if repo_credentials.access_token:
                extras.append(repo_credentials.access_token)
            error_description = redact(str(e), extras)
            await dependencies.event_store.append(
                process_id,
                EnvironmentValidationFailed(
                    process_id=process_id,
                    occurred_at=dependencies.clock.now(),
                    stdout="",
                    stderr=f"[phase=global_setup] {error_description}",
                    return_code=extract_exit_code(error_description, default=1),
                ),
            )
            return
        try:
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
        except Exception as e:
            extras = [cmd, repo_credentials.url]
            if repo_credentials.access_token:
                extras.append(repo_credentials.access_token)
            error_description = redact(str(e), extras)
            await dependencies.event_store.append(
                process_id,
                EnvironmentValidationFailed(
                    process_id=process_id,
                    occurred_at=dependencies.clock.now(),
                    stdout="",
                    stderr=f"[phase=project_setup] {error_description}",
                    return_code=extract_exit_code(error_description, default=1),
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


def extract_exit_code(msg: str, default: int = 1) -> int:
    m = re.search(r"exit code (\d+)", msg)
    return int(m.group(1)) if m else default


REDACTIONS = [
    # 1) Explicit token prefixes
    (re.compile(r"\bsk-[A-Za-z0-9-]{16,}\b"), "[REDACTED]"),  # OpenAI-ish
    (re.compile(r"\bsk-ant-[A-Za-z0-9-]{16,}\b"), "[REDACTED]"),  # Anthropic
    (re.compile(r"\bgh[pso]_[A-Za-z0-9]{20,}\b"), "[REDACTED]"),  # GitHub
    (re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}\b"), "[REDACTED]"),  # GitLab PAT
    (re.compile(r"\bjira[a-z0-9_]{10,}\b", re.I), "[REDACTED]"),  # example extra
    # 2) Bearer/JWT
    (
        re.compile(r"(?i)(Authorization:\s*Bearer\s+)[A-Za-z0-9._-]{10,}"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        "[REDACTED]",
    ),  # JWT
    # 3) Env-var style assignments (OPENAI/ANTHROPIC/MORPHCLOUD API KEY)
    (
        re.compile(
            r"(?i)\b(?P<var>(?:OPENAI|ANTHROPIC|MORPHCLOUD)[-_ ]?API[-_ ]?KEY)\b\s*[:=]\s*(?P<q>['\"])[^'\"\s]+(?P=q)"
        ),
        r"\g<var>=\g<q>[REDACTED]\g<q>",
    ),
    (
        re.compile(
            r"(?i)\b(?P<var>[A-Z0-9_]*API[_-]?KEY)\b\s*[:=]\s*(?P<q>['\"])[^'\"\s]+(?P=q)"
        ),
        r"\g<var>=\g<q>[REDACTED]\g<q>",
    ),
    # 4) Creds in URLs
    (re.compile(r"https?://[^/\s:@]+:[^@\s]+@"), "https://[REDACTED]@"),
    (re.compile(r"(?i)([?&](?:token|access_token|api_key)=[^&\s]+)"), "[REDACTED]"),
]


def redact(text: str, extras: list[str] | None = None) -> str:
    out = text or ""
    for v in filter(None, (extras or [])):
        out = out.replace(v, "[REDACTED]")
    for rx, repl in REDACTIONS:
        out = rx.sub(repl, out)
    return out


class EnvironmentSetupError(Exception):
    pass
