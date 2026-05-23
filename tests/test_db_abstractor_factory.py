"""
Tests for genericsuite/util/db_abstractor.py — factory helpers and
verify_required_fields (pure function, no live DB needed).

All mocking and imports are done INSIDE test functions so that module-level
execution during pytest collection does not contaminate sys.modules for the
supabase/postgresql test files (which are collected later alphabetically).
"""
import sys
from unittest.mock import MagicMock


def _import_db_abstractor():
    """Import db_abstractor with all dependencies stubbed."""
    import types as _t
    from unittest.mock import MagicMock

    _bson = MagicMock()
    _bson.json_util = MagicMock()
    _bson.json_util.dumps = lambda x: str(x)
    _bson.json_util.ObjectId = str
    sys.modules.setdefault("bson", _bson)
    sys.modules.setdefault("bson.json_util", _bson.json_util)
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

    wl_mock = MagicMock()
    wl_mock.LocalProxy = lambda fn: fn()
    sys.modules.setdefault("werkzeug.local", wl_mock)

    for _mod in [
        "genericsuite.util.db_abstractor_mongodb",
        "genericsuite.util.db_abstractor_dynamodb",
        "genericsuite.util.db_abstractor_postgresql",
        "genericsuite.util.db_abstractor_mysql",
        "genericsuite.util.db_abstractor_supabase",
        "genericsuite.util.db_abstractor_super",
        "genericsuite.util.request_handler",
    ]:
        sys.modules.setdefault(_mod, MagicMock())

    _cfg_mod = _t.ModuleType("genericsuite.config.config")

    class _StubConfig:
        APP_SECRET_KEY = "k"
        DB_ENGINE = "MONGODB"
        DB_CONFIG = {"app_db_uri": "fake", "app_db_name": "test", "dynamdb_prefix": ""}

    _cfg_mod.Config = _StubConfig
    sys.modules.setdefault("genericsuite.config.config", _cfg_mod)

    for _mod in list(sys.modules):
        if "genericsuite.util.db_abstractor" == _mod:
            del sys.modules[_mod]

    from genericsuite.util.db_abstractor import verify_required_fields, set_db_request
    return verify_required_fields, set_db_request


# ---- verify_required_fields (pure function) ----

def test_verify_required_fields_all_present():
    verify_required_fields, _ = _import_db_abstractor()
    fields = {"name": "Alice", "email": "a@b.com"}
    result = verify_required_fields(fields, ["name", "email"], "TEST-001")
    assert result["error"] is False
    assert result["error_message"] == ""


def test_verify_required_fields_missing_one():
    verify_required_fields, _ = _import_db_abstractor()
    fields = {"name": "Alice"}
    result = verify_required_fields(fields, ["name", "email"], "TEST-002")
    assert result["error"] is True
    assert "email" in result["error_message"]
    assert "TEST-002" in result["error_message"]


def test_verify_required_fields_missing_multiple():
    verify_required_fields, _ = _import_db_abstractor()
    fields = {}
    result = verify_required_fields(fields, ["a", "b", "c"], "E001")
    assert result["error"] is True
    assert "a" in result["error_message"]
    assert "b" in result["error_message"]
    assert "c" in result["error_message"]


def test_verify_required_fields_empty_required_list():
    verify_required_fields, _ = _import_db_abstractor()
    result = verify_required_fields({"x": 1}, [], "E000")
    assert result["error"] is False


def test_verify_required_fields_returns_result_dict():
    verify_required_fields, _ = _import_db_abstractor()
    result = verify_required_fields({}, [], "X")
    assert "error" in result
    assert "error_message" in result
    assert "resultset" in result


# ---- set_db_request ----

def test_set_db_request_stores_request():
    _, set_db_request = _import_db_abstractor()
    mock_req = MagicMock()
    set_db_request(mock_req)
    assert True  # no exception raised
