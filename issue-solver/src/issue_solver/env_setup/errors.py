import re
from dataclasses import dataclass
from enum import Enum

from issue_solver.security.redactions import redact


def extract_exit_code(msg: str, default: int = 1) -> int:
    m = re.search(r"exit code (\d+)", msg)
    return int(m.group(1)) if m else default


class Phase(str, Enum):
    GLOBAL_SETUP = "global_setup"
    PROJECT_SETUP = "project_setup"


@dataclass(slots=True)
class EnvironmentSetupError(RuntimeError):
    phase: Phase
    exit_code: int
    stderr: str  # already redacted, safe to persist
    raw_error: str  # original (avoid persisting this)

    @classmethod
    def from_exception(
        cls, phase: Phase, exc: Exception, extras: list[str], redact_fn=redact
    ) -> "EnvironmentSetupError":
        raw = str(exc)
        rc = extract_exit_code(raw, default=1)
        safe = redact_fn(raw, extras)
        return cls(phase=phase, exit_code=rc, stderr=safe, raw_error=raw)
