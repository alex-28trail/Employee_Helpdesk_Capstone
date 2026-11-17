"""Logging setup (F1.4).

Rules the whole backend follows:
- Log events as `event=<name> key=value ...` with IDs, enum values and timings only.
- Never log ticket titles/descriptions, raw model output, passwords or connection strings.
The RedactingFilter is a safety net in case something sensitive slips into a message.
"""
import logging
import re
import sys

_REDACTIONS = [
    # postgresql://user:password@host  ->  postgresql://user:***@host
    (re.compile(r"(\b[a-z][a-z0-9+.\-]*://[^:/\s@]+:)[^@\s]+@", re.I), r"\1***@"),
    # password=..., token: ..., api_key=...
    (re.compile(r"\b(password|passwd|pwd|secret|token|api[_-]?key)\b(\s*[:=]\s*)\S+", re.I), r"\1\2***"),
    (re.compile(r"\bbearer\s+[a-z0-9._\-]+", re.I), "Bearer ***"),
]


def redact(text: str) -> str:
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = None
        return True


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    handler.addFilter(RedactingFilter())

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())

    # httpx logs every request URL at INFO; keep it quiet.
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
