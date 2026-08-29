"""
Tests for genericsuite/models/menu_options/menu_options.py and security.py
menu authorization logic.
"""
import sys
from unittest.mock import MagicMock

sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_db_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_endpoint_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.app_context", MagicMock())

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
_util_mock.return_resultset_jsonified_or_exception = MagicMock(return_value={})
_util_mock.get_query_params = MagicMock(return_value={})
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)


def test_menu_options_module_importable():
    import genericsuite.models.menu_options.menu_options as m
    assert m is not None


# ---- Authorization logic tested via security.py (no DB needed) ----

def test_full_menu_for_admin():
    """Authorize_menu_options returns all entries for admin group."""
    # Import fresh to avoid cross-test contamination
    _sec_mock = sys.modules.get("genericsuite.util.security")
    if _sec_mock and isinstance(_sec_mock, MagicMock):
        del sys.modules["genericsuite.util.security"]

    from genericsuite.util.security import authorize_menu_options
    menu = [
        {"name": "dashboard"},
        {"name": "admin-only", "sec_group": "admin"},
        {"name": "users-only", "sec_group": "users"},
    ]
    result = authorize_menu_options(menu, ["admin", "users"])
    names = [item["name"] for item in result]
    assert "dashboard" in names
    assert "admin-only" in names
    assert "users-only" in names


def test_filtered_menu_for_regular_user():
    """Regular user should not see admin items."""
    from genericsuite.util.security import authorize_menu_options
    menu = [
        {"name": "dashboard"},
        {"name": "admin-panel", "sec_group": "admin"},
    ]
    result = authorize_menu_options(menu, ["users"])
    names = [item["name"] for item in result]
    assert "dashboard" in names
    assert "admin-panel" not in names
