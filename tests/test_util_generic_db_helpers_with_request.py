"""
Tests for genericsuite/util/generic_db_helpers_with_request.py.
"""
import sys
from unittest.mock import MagicMock

_bson = MagicMock()
_bson.json_util = MagicMock()
_bson.json_util.dumps = lambda x: str(x)
_bson.json_util.ObjectId = str
sys.modules.setdefault("bson", _bson)
sys.modules.setdefault("bson.json_util", _bson.json_util)
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)
sys.modules.setdefault("genericsuite.util.db_abstractor", MagicMock())
sys.modules.setdefault("genericsuite.util.db_abstractor_super", MagicMock())
sys.modules.setdefault("genericsuite.util.config_dbdef_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.current_user_data", MagicMock())
sys.modules.setdefault("genericsuite.util.jwt", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_db_helpers_super", MagicMock())


def test_generic_db_helpers_with_request_importable():
    import genericsuite.util.generic_db_helpers_with_request as m
    assert m is not None


def test_generic_db_helper_with_request_class_exists():
    from genericsuite.util.generic_db_helpers_with_request import \
        GenericDbHelperWithRequest
    assert GenericDbHelperWithRequest is not None
