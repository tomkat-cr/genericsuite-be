"""
Tests for genericsuite/util/generic_db_helpers.py — GenericDbHelper.
"""
import sys
from unittest.mock import MagicMock, patch

# Mock all heavy imports before touching generic_db_helpers
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
_util_mock.get_standard_base_exception_msg = lambda e, code: f"ERR {code}: {e}"
_util_mock.email_verification = MagicMock(return_value={"error_message": None})
_util_mock.sort_list_of_dicts = lambda lst, *a, **kw: lst
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)

_dt_mock = MagicMock()
_dt_mock.current_datetime_timestamp.return_value = 1_700_000_000.0
_dt_mock.get_date_range_filter = MagicMock(return_value={})
sys.modules.setdefault("genericsuite.util.datetime_utilities", _dt_mock)

sys.modules.setdefault("genericsuite.util.nav_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.passwords", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_db_helpers_with_request", MagicMock())

_db_abs_mock = MagicMock()
_db_abs_mock.verify_required_fields = MagicMock(return_value={"error": False, "error_message": None})
_db_abs_mock.get_order_direction = MagicMock(return_value=1)
sys.modules.setdefault("genericsuite.util.db_abstractor", _db_abs_mock)


def test_generic_db_helper_module_importable():
    """The module must import without error."""
    import genericsuite.util.generic_db_helpers as m
    assert m is not None


def test_generic_db_helper_class_exists():
    from genericsuite.util.generic_db_helpers import GenericDbHelper
    assert GenericDbHelper is not None


def test_generic_db_helper_class_importable_from_module():
    """GenericDbHelper symbol is accessible from the module."""
    import genericsuite.util.generic_db_helpers as m
    assert hasattr(m, "GenericDbHelper")
