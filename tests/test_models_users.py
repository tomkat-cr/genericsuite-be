"""
Tests for genericsuite/models/users/users.py.
"""
import sys
from unittest.mock import MagicMock

# Stub all heavy deps
_bson = MagicMock()
_bson.json_util = MagicMock()
_bson.json_util.dumps = lambda x: str(x)
_bson.json_util.ObjectId = str
sys.modules.setdefault("bson", _bson)
sys.modules.setdefault("bson.json_util", _bson.json_util)
sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault("genericsuite.util.db_abstractor", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_db_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_endpoint_helpers", MagicMock())
sys.modules.setdefault("genericsuite.config.config_from_db", MagicMock())
sys.modules.setdefault("genericsuite.constants.const_tables", MagicMock())

_jwt_mock = MagicMock()
_jwt_mock.token_encode = MagicMock(return_value="fake.jwt.token")
_jwt_mock.get_basic_auth = MagicMock(return_value={"error": False, "resultset": {"user": "u", "password": "p"}})
_jwt_mock.AuthorizedRequest = MagicMock
sys.modules.setdefault("genericsuite.util.jwt", _jwt_mock)

_passwords_mock = MagicMock()
_passwords_mock.Passwords = MagicMock()
_passwords_mock.Passwords.return_value.encrypt_password = MagicMock(return_value="hashed")
sys.modules.setdefault("genericsuite.util.passwords", _passwords_mock)

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
_util_mock.return_resultset_jsonified_or_exception = MagicMock(return_value={})
_util_mock.get_id_as_string = str
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)

import types
_cfg_mod = types.ModuleType("genericsuite.config.config")


class _StubCfg:
    HEADER_TOKEN_ENTRY_NAME = "x-access-token"
    APP_SECRET_KEY = "fake"
    APP_SUPERADMIN_EMAIL = "admin@test.com"


_cfg_mod.Config = _StubCfg
sys.modules["genericsuite.config.config"] = _cfg_mod


def test_users_module_importable():
    import genericsuite.models.users.users as m
    assert m is not None


def test_users_crud_function_exists():
    import genericsuite.models.users.users as m
    assert hasattr(m, "users_crud")


def test_login_user_function_exists():
    import genericsuite.models.users.users as m
    assert hasattr(m, "login_user")
