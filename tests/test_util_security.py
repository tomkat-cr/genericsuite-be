"""
Tests for genericsuite/util/security.py — user groups and menu authorization.
"""
import sys
from unittest.mock import MagicMock

# Mock all framework-dependent modules before importing security
sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault("genericsuite.util.app_context", MagicMock())
sys.modules.setdefault("genericsuite.util.generic_endpoint_helpers", MagicMock())

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
_util_mock.get_query_params = MagicMock(return_value={})
_util_mock.get_request_body = MagicMock(return_value={})
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)

from genericsuite.util.security import (
    get_user_groups,
    authorize_menu_options,
    get_user_authorized_menu,
)


# ---- get_user_groups ----

def test_get_user_groups_includes_users_always():
    user_data = {}
    groups = get_user_groups(user_data)
    assert "users" in groups


def test_get_user_groups_includes_explicit_groups():
    user_data = {"groups": ["editors"]}
    groups = get_user_groups(user_data)
    assert "editors" in groups


def test_get_user_groups_superuser_gets_admin():
    user_data = {"superuser": "1"}
    groups = get_user_groups(user_data)
    assert "admin" in groups


def test_get_user_groups_non_superuser_no_admin():
    user_data = {"superuser": "0"}
    groups = get_user_groups(user_data)
    assert "admin" not in groups


# ---- authorize_menu_options ----

def test_authorize_menu_options_includes_ungrouped_items():
    menu = [{"name": "home"}]
    result = authorize_menu_options(menu, ["users"])
    assert len(result) == 1


def test_authorize_menu_options_excludes_restricted_group():
    menu = [{"name": "admin-panel", "sec_group": "admin"}]
    result = authorize_menu_options(menu, ["users"])
    assert len(result) == 0


def test_authorize_menu_options_includes_matching_group():
    menu = [{"name": "admin-panel", "sec_group": "admin"}]
    result = authorize_menu_options(menu, ["admin", "users"])
    assert len(result) == 1


def test_authorize_menu_options_recurses_sub_menus():
    menu = [{
        "name": "reports",
        "sub_menu_options": [
            {"name": "public-report"},
            {"name": "secret-report", "sec_group": "admin"},
        ]
    }]
    result = authorize_menu_options(menu, ["users"])
    assert len(result) == 1
    assert len(result[0]["sub_menu_options"]) == 1
    assert result[0]["sub_menu_options"][0]["name"] == "public-report"


# ---- get_user_authorized_menu ----

def test_get_user_authorized_menu_returns_resultset():
    menu_data = [{"name": "home"}]
    user_data = {}
    result = get_user_authorized_menu(menu_data, user_data)
    assert "resultset" in result
