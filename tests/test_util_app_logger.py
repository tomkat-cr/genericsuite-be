"""
Tests for genericsuite/util/app_logger.py — sanitize_log_message and loggers.
"""
import sys
import types
from unittest.mock import MagicMock, patch

# Ensure a fresh load of app_logger using a stub Config
for _mod in list(sys.modules):
    if "genericsuite.util.app_logger" in _mod:
        del sys.modules[_mod]

_cfg_mod = types.ModuleType("genericsuite.config.config")
_cfg_mod.is_local_service = lambda: False


class _StubConfig:
    APP_NAME = "test_app"
    DEBUG = False


_cfg_mod.Config = _StubConfig
sys.modules["genericsuite.config.config"] = _cfg_mod

import os
os.environ.setdefault("APP_DB_ENGINE", "MONGODB")
os.environ.setdefault("APP_DB_NAME", "mongo")

from genericsuite.util.app_logger import (
    sanitize_log_message,
    log_debug,
    log_info,
    log_warning,
    log_error,
)


# ---- sanitize_log_message ----

def test_sanitize_strips_newline():
    assert "\n" not in sanitize_log_message("line1\nline2")


def test_sanitize_strips_carriage_return():
    assert "\r" not in sanitize_log_message("attack\rCRITICAL")


def test_sanitize_combined_crlf():
    result = sanitize_log_message("a\r\nb")
    assert "\n" not in result and "\r" not in result


def test_sanitize_none_returns_empty():
    assert sanitize_log_message(None) == ""


def test_sanitize_int_coerces_to_str():
    assert sanitize_log_message(42) == "42"


def test_sanitize_clean_string_unchanged():
    assert sanitize_log_message("hello world") == "hello world"


# ---- log functions return a formatted string ----

def test_log_info_returns_string():
    result = log_info("test message")
    assert isinstance(result, str)
    assert "test message" in result


def test_log_error_returns_string():
    result = log_error("error happened")
    assert isinstance(result, str)
    assert "error happened" in result


def test_log_warning_returns_string():
    result = log_warning("warning msg")
    assert isinstance(result, str)


def test_log_debug_returns_string():
    result = log_debug("debug info")
    assert isinstance(result, str)
