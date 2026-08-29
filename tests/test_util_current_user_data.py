"""
Tests for genericsuite/util/current_user_data.py.
"""
import sys
from unittest.mock import MagicMock

# Remove cached module to get a fresh import
for _mod in list(sys.modules):
    if "genericsuite.util.current_user_data" in _mod:
        del sys.modules[_mod]

# Set up mocks using direct assignment (not setdefault)
_fw_mock = MagicMock()
_fw_mock.get_current_framework = MagicMock(return_value="fastapi")
_fw_mock.Request = MagicMock
sys.modules["genericsuite.util.framework_abs_layer"] = _fw_mock

sys.modules["genericsuite.util.app_logger"] = MagicMock()

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
_util_mock.error_resultset = lambda msg, code="": {
    "error": True, "error_message": msg, "resultset": {}, "totalPages": None
}
sys.modules["genericsuite.util.utilities"] = _util_mock

_db_helper_mock = MagicMock()
sys.modules["genericsuite.util.generic_db_helpers"] = _db_helper_mock

_jwt_mock = MagicMock()
_jwt_mock.AuthorizedRequest = MagicMock
sys.modules["genericsuite.util.jwt"] = _jwt_mock

from genericsuite.util.current_user_data import (
    get_curr_user_id,
    get_curr_user_data,
    NON_AUTH_REQUEST_USER_ID,
)


def _make_authorized_request(user_id: str):
    req = MagicMock()
    req.user = MagicMock()
    req.user.public_id = user_id
    return req


def _make_plain_request():
    """A request object without a 'user' attribute."""
    req = MagicMock(spec=["method", "headers", "json_body"])
    return req


def test_get_curr_user_id_from_authorized_request():
    req = _make_authorized_request("abc123")
    uid = get_curr_user_id(req)
    assert uid == "abc123"


def test_get_curr_user_id_non_auth_request():
    req = _make_plain_request()
    uid = get_curr_user_id(req)
    assert uid == NON_AUTH_REQUEST_USER_ID


def test_non_auth_request_user_id_constant():
    assert NON_AUTH_REQUEST_USER_ID == "[N/A/R]"


def test_get_curr_user_data_non_auth_returns_no_error():
    req = _make_plain_request()
    blueprint = MagicMock()
    result = get_curr_user_data(req, blueprint)
    assert result["error"] is False
