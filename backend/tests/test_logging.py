"""Logging must not leak credentials (F1.4)."""
import logging

from app.logging_config import RedactingFilter, redact


def test_connection_string_password_is_redacted():
    text = redact("db=postgresql+psycopg://helpdesk:S3cret!@localhost:5432/helpdesk")
    assert "S3cret" not in text and "helpdesk:***@" in text


def test_key_value_secrets_are_redacted():
    assert "abc123" not in redact("password=abc123 token: abc123 api_key=abc123")


def test_filter_redacts_formatted_args():
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "connecting to %s", ("postgresql://u:pw@h/db",), None)
    RedactingFilter().filter(record)
    assert "pw@" not in record.getMessage()
