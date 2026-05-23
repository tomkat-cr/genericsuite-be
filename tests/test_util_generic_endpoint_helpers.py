"""
Tests for genericsuite/util/generic_endpoint_helpers.py — GenericEndpointHelper.
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
sys.modules.setdefault("genericsuite.util.app_context", MagicMock())
sys.modules.setdefault("genericsuite.util.nav_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_db_helpers", MagicMock())

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
_util_mock.get_query_params = MagicMock(return_value={})
_util_mock.get_request_body = MagicMock(return_value={})
_util_mock.return_resultset_jsonified_or_exception = MagicMock(return_value={})
_util_mock.method_not_allowed = MagicMock(return_value={"error": True})
_util_mock.error_resultset = lambda msg, code="": {
    "error": True, "error_message": msg, "resultset": {}, "totalPages": None
}
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)


def test_generic_endpoint_helpers_importable():
    import genericsuite.util.generic_endpoint_helpers as m
    assert m is not None


def test_generic_endpoint_helper_class_exists():
    from genericsuite.util.generic_endpoint_helpers import GenericEndpointHelper
    assert GenericEndpointHelper is not None
