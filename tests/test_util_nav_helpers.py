"""
Tests for genericsuite/util/nav_helpers.py — pagination helpers.
"""
import sys
import json
from unittest.mock import MagicMock

sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

_util_mock = MagicMock()
_util_mock.get_query_params = MagicMock(return_value={})
_util_mock.get_standard_base_exception_msg = lambda e, code: f"ERR {code}: {e}"
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)

for _mod in list(sys.modules):
    if "genericsuite.util.nav_helpers" == _mod:
        del sys.modules[_mod]

from genericsuite.util.nav_helpers import (
    get_total_pages,
    put_total_pages_from_resultset,
    put_total_pages_in_resultset,
)


# ---- get_total_pages ----

def test_get_total_pages_exact_division():
    assert get_total_pages(100, 10) == 10


def test_get_total_pages_with_remainder():
    assert get_total_pages(101, 10) == 11


def test_get_total_pages_zero_limit_returns_one():
    assert get_total_pages(500, 0) == 1


def test_get_total_pages_zero_rows():
    assert get_total_pages(0, 10) == 0


def test_get_total_pages_less_than_one_page():
    assert get_total_pages(5, 10) == 1


# ---- put_total_pages_from_resultset ----

def test_put_total_pages_from_resultset_success():
    rs = {
        "error": False,
        "error_message": None,
        "resultset": json.dumps([{"id": 1}, {"id": 2}, {"id": 3}]),
        "totalPages": None,
    }
    result = put_total_pages_from_resultset(2, rs)
    assert result["totalPages"] == 2  # 3 items / limit 2 = 2 pages


def test_put_total_pages_from_resultset_error_passthrough():
    rs = {"error": True, "error_message": "bad", "resultset": None, "totalPages": None}
    result = put_total_pages_from_resultset(10, rs)
    assert result["error"] is True
    assert result["totalPages"] is None


# ---- put_total_pages_in_resultset ----

def test_put_total_pages_in_resultset_success():
    mock_collection = MagicMock()
    mock_collection.count_documents.return_value = 25
    rs = {"error": False, "error_message": None, "resultset": [], "totalPages": None}
    result = put_total_pages_in_resultset(mock_collection, {}, 10, rs, "T001")
    assert result["totalPages"] == 3  # ceil(25/10)


def test_put_total_pages_in_resultset_error_passthrough():
    mock_collection = MagicMock()
    rs = {"error": True, "error_message": "oops", "resultset": None, "totalPages": None}
    result = put_total_pages_in_resultset(mock_collection, {}, 10, rs, "T002")
    assert result["error"] is True
    mock_collection.count_documents.assert_not_called()
