"""
Tests for genericsuite.util.send_email critical validation and safety paths.
"""
import sys
from unittest.mock import MagicMock, patch

from genericsuite.util.send_email import parse_recipients, send_email
import genericsuite.util.send_email as send_email_mod

# Avoid framework circular imports when loading utilities via send_email
for _mod in list(sys.modules):
    if "genericsuite.util.send_email" in _mod \
            or "genericsuite.util.utilities" in _mod:
        del sys.modules[_mod]

_fw_mock = MagicMock()
_fw_mock.Response = MagicMock
_fw_mock.Request = MagicMock
sys.modules["genericsuite.util.framework_abs_layer"] = _fw_mock
sys.modules["genericsuite.util.app_logger"] = MagicMock()


def test_parse_recipients_splits_and_dedupes():
    assert parse_recipients("a@x.com, b@x.com", ["b@x.com", "c@x.com"]) == [
        "a@x.com",
        "b@x.com",
        "c@x.com",
    ]


def test_send_email_missing_sender_returns_error_not_attribute_error(monkeypatch):  # noqa: E501
    monkeypatch.delenv("SMTP_DEFAULT_SENDER", raising=False)
    result = send_email(
        None,
        "to@example.com",
        "Subject",
        "plain",
        "",
    )
    assert result["error"] is True
    assert "Sender email is required" in result["error_message"]


def test_send_email_blank_sender_returns_error(monkeypatch):
    monkeypatch.delenv("SMTP_DEFAULT_SENDER", raising=False)
    result = send_email(
        "   ",
        "to@example.com",
        "Subject",
        "plain",
        "",
    )
    assert result["error"] is True
    assert "Sender email is required" in result["error_message"]


def test_send_email_missing_smtp_config_returns_error(monkeypatch):
    for key in ("SMTP_SERVER", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    result = send_email(
        "from@example.com",
        "to@example.com",
        "Subject",
        "plain",
        "",
    )
    assert result["error"] is True
    assert "SMTP_SERVER" in result["error_message"]
    assert "SMTP_PORT" in result["error_message"]
    assert "SMTP_USER" in result["error_message"]
    assert "SMTP_PASSWORD" in result["error_message"]


def test_send_email_invalid_smtp_port_returns_error(monkeypatch):
    monkeypatch.setenv("SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "not-a-port")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    result = send_email(
        "from@example.com",
        "to@example.com",
        "Subject",
        "plain",
        "",
    )
    assert result["error"] is True
    assert "SMTP_PORT" in result["error_message"]


def test_send_email_debug_with_missing_password_does_not_crash(monkeypatch):
    monkeypatch.setenv("SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.setattr(send_email_mod, "DEBUG", True)

    result = send_email(
        "from@example.com",
        "to@example.com",
        "Subject",
        "plain",
        "",
    )
    assert result["error"] is True
    assert "SMTP_PASSWORD" in result["error_message"]


@patch("genericsuite.util.send_email.smtplib.SMTP")
def test_send_email_uses_context_manager_and_utf8(mock_smtp_cls, monkeypatch):
    monkeypatch.setenv("SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")

    smtp_instance = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = smtp_instance
    mock_smtp_cls.return_value.__exit__.return_value = None

    result = send_email(
        "from@example.com",
        ["to@example.com", "cc@example.com"],
        "Asunto cafe",
        "Hola nino",
        "<p>Hola nino</p>",
    )

    assert result["error"] is False
    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("user", "secret")
    smtp_instance.sendmail.assert_called_once()
    args = smtp_instance.sendmail.call_args[0]
    assert args[0] == "from@example.com"
    assert args[1] == ["to@example.com", "cc@example.com"]
    raw_message = args[2]
    assert "charset=\"utf-8\"" in raw_message or "charset=utf-8" in raw_message
