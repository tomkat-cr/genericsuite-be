"""
Tests for genericsuite/util/send_email.py — remove_html_tags (pure).
"""
import sys
from unittest.mock import MagicMock

# send_email imports Config and smtplib — mock both
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

import types as _t
_cfg_mod = _t.ModuleType("genericsuite.config.config")


class _StubConfig:
    SMTP_SERVER = "smtp.example.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "user@example.com"
    SMTP_PASSWORD = "pass"
    APP_NAME = "test_app"


_cfg_mod.Config = _StubConfig
sys.modules.setdefault("genericsuite.config.config", _cfg_mod)
sys.modules.setdefault("smtplib", MagicMock())

for _mod in list(sys.modules):
    if "genericsuite.util.send_email" == _mod:
        del sys.modules[_mod]

from genericsuite.util.send_email import remove_html_tags


def test_remove_html_tags_basic():
    result = remove_html_tags("<p>Hello <b>world</b></p>")
    assert result == "Hello world"


def test_remove_html_tags_no_tags():
    result = remove_html_tags("plain text")
    assert result == "plain text"


def test_remove_html_tags_empty_string():
    result = remove_html_tags("")
    assert result == ""


def test_remove_html_tags_nested():
    result = remove_html_tags("<div><span>text</span></div>")
    assert result == "text"


def test_remove_html_tags_self_closing():
    result = remove_html_tags("line1<br/>line2")
    assert "line1" in result
    assert "line2" in result
