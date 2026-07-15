"""
Tests for genericsuite/util/jwt.py — token_encode, get_basic_auth,
generate_access_token (no live DB needed).
"""
import sys
import os
import types
import base64
from unittest.mock import MagicMock, patch

# Clean any cached mocked version
for _mod in list(sys.modules):
    if "genericsuite.util.jwt" == _mod:
        del sys.modules[_mod]

# Set up mocks using direct assignment
_fw_mock = MagicMock()
_fw_mock.Request = MagicMock
_fw_mock.get_current_framework = MagicMock(return_value="fastapi")
sys.modules["genericsuite.util.framework_abs_layer"] = _fw_mock

sys.modules["genericsuite.util.app_logger"] = MagicMock()

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
_util_mock.standard_error_return = lambda msg, **kw: {
    "error": True, "error_message": msg, "resultset": {}, "totalPages": None
}
_util_mock.get_default_resultset.side_effect = lambda: {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
_util_mock.error_resultset = lambda msg, **kw: {
    "error": True, "error_message": msg, "resultset": {}, "totalPages": None
}
_util_mock.get_id_as_string = lambda row: str(row.get("_id", "test_id"))
sys.modules["genericsuite.util.utilities"] = _util_mock

_super_mock = MagicMock()
# Use setdefault (not direct assignment) so this doesn't clobber the real
# module, or another test's mock, if it was already imported earlier in
# the same pytest session (module-level test mocking is process-global).
sys.modules.setdefault(
    "genericsuite.util.generic_db_helpers_super", _super_mock)

import types as _t
_cfg_mod = _t.ModuleType("genericsuite.config.config")
os.environ.setdefault("APP_SECRET_KEY", "fake_secret_key_for_tests_only")
os.environ.setdefault("EXPIRATION_MINUTES", "30")
os.environ.setdefault("TEMP_DIR", "/tmp")


class _StubConfig:
    APP_SECRET_KEY = "fake_secret_key_for_tests_only"
    HEADER_TOKEN_ENTRY_NAME = "x-access-token"
    APP_SUPERADMIN_EMAIL = "admin@test.com"


_cfg_mod.Config = _StubConfig
sys.modules["genericsuite.config.config"] = _cfg_mod

from genericsuite.util.jwt import (
    generate_access_token,
    token_encode,
    get_basic_auth,
)


# ---- generate_access_token ----

def test_generate_access_token_returns_string():
    token = generate_access_token()
    assert isinstance(token, str)
    assert len(token) > 0


def test_generate_access_token_default_length():
    token = generate_access_token()
    # 64 bytes hex = 128 chars
    assert len(token) == 128


def test_generate_access_token_custom_length():
    token = generate_access_token(length=32)
    assert len(token) == 64  # 32 bytes hex = 64 chars


def test_generate_access_token_unique():
    t1 = generate_access_token()
    t2 = generate_access_token()
    assert t1 != t2


# ---- token_encode ----

def test_token_encode_returns_string():
    user = {"_id": "user123"}
    token = token_encode(user)
    assert isinstance(token, str)
    assert len(token) > 10


def test_token_encode_is_valid_jwt():
    import jwt as pyjwt
    user = {"_id": "user123"}
    token = token_encode(user)
    decoded = pyjwt.decode(
        token,
        "fake_secret_key_for_tests_only",
        algorithms=["HS256"]
    )
    assert "public_id" in decoded
    assert decoded["public_id"] == "user123"


def test_token_encode_different_users_produce_different_tokens():
    t1 = token_encode({"_id": "user1"})
    t2 = token_encode({"_id": "user2"})
    assert t1 != t2


# ---- get_basic_auth ----

def _make_basic_auth_header(user: str, password: str) -> str:
    credentials = f"{user}:{password}"
    encoded = base64.b64encode(credentials.encode("ascii")).decode("ascii")
    return f"Basic {encoded}"


def test_get_basic_auth_valid():
    header = _make_basic_auth_header("testuser", "testpass")
    result = get_basic_auth(header)
    assert result["error"] is False
    assert result["resultset"]["user"] == "testuser"
    assert result["resultset"]["password"] == "testpass"


def test_get_basic_auth_password_with_colon():
    header = _make_basic_auth_header("user", "pass:with:colons")
    result = get_basic_auth(header)
    assert result["error"] is False
    assert result["resultset"]["password"] == "pass:with:colons"


def test_get_basic_auth_missing_basic_prefix():
    result = get_basic_auth("Bearer sometoken")
    assert result["error"] is True
    assert "Authorization Required" in result["error_message"]


def test_get_basic_auth_empty_string():
    result = get_basic_auth("")
    assert result["error"] is True
