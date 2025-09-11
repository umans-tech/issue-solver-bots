import re

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


def redact(text: str, exact_values_to_redact: list[str] | None = None) -> str:
    out = text or ""
    for v in filter(None, (exact_values_to_redact or [])):
        out = out.replace(v, "[REDACTED]")
    for rx, repl in REDACTIONS:
        out = rx.sub(repl, out)
    return out
