"""
Tests for genericsuite/models/logs/logs.py.
"""
import sys
from unittest.mock import MagicMock

_bson = MagicMock()
_bson.json_util = MagicMock()
_bson.json_util.dumps = lambda x: str(x)
sys.modules.setdefault("bson", _bson)
sys.modules.setdefault("bson.json_util", _bson.json_util)
sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_db_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_endpoint_helpers", MagicMock())

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
_util_mock.return_resultset_jsonified_or_exception = MagicMock(return_value={})
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)


def test_logs_module_importable():
    import genericsuite.models.logs.logs as m
    assert m is not None
