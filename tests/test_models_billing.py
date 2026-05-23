"""
Tests for genericsuite/models/billing/billing_utilities.py.
"""
import sys
from unittest.mock import MagicMock

sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_db_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_endpoint_helpers", MagicMock())

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)


def test_billing_utilities_importable():
    import genericsuite.models.billing.billing_utilities as m
    assert m is not None
