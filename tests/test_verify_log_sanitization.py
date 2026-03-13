"""
Pytest tests for log message sanitization (no unittest).
"""
import sys
import types

# Force a fresh import of app_logger so we get the real implementation
# (other test modules may have replaced it with a MagicMock)
for mod in list(sys.modules):
    if mod == "genericsuite.util.app_logger" or mod.startswith("genericsuite.util.app_logger."):
        del sys.modules[mod]

# Mock config so app_logger can load without env (Config() at module level)
_config_module = types.ModuleType("genericsuite.config.config")
_config_module.is_local_service = lambda: True


class _MockConfig:
    APP_NAME = "test_app"
    DEBUG = False


_config_module.Config = _MockConfig
if "genericsuite.config" not in sys.modules:
    sys.modules["genericsuite.config"] = types.ModuleType("genericsuite.config")
sys.modules["genericsuite.config.config"] = _config_module

from genericsuite.util.app_logger import sanitize_log_message


def test_sanitize_newline():
    msg = "User logged in\nAdmin: YES"
    assert sanitize_log_message(msg) == "User logged in\\nAdmin: YES"


def test_sanitize_carriage_return():
    msg = "Attack payload\rCRITICAL"
    assert sanitize_log_message(msg) == "Attack payload\\rCRITICAL"


def test_sanitize_newline_and_cr():
    msg = "Line 1\r\nLine 2"
    assert sanitize_log_message(msg) == "Line 1\\r\\nLine 2"


def test_sanitize_none_returns_empty():
    assert sanitize_log_message(None) == ""


def test_sanitize_int_coerced_to_str():
    assert sanitize_log_message(123) == "123"


def test_sanitize_safe_message_unchanged():
    msg = "Normal message"
    assert sanitize_log_message(msg) == "Normal message"
