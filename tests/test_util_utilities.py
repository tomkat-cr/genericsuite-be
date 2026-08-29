"""
Tests for genericsuite/util/utilities.py — core helper functions.
"""
import sys
import types
from unittest.mock import MagicMock

# Remove any cached mocked version of utilities
for _mod in list(sys.modules):
    if "genericsuite.util.utilities" in _mod:
        del sys.modules[_mod]

# Set up required mocks using direct assignment
_fw_mock = MagicMock()
_fw_mock.Response = MagicMock
_fw_mock.Request = MagicMock
sys.modules["genericsuite.util.framework_abs_layer"] = _fw_mock
sys.modules["genericsuite.util.app_logger"] = MagicMock()

_cfg_mod = types.ModuleType("genericsuite.config.config")


class _StubConfig:
    APP_SECRET_KEY = "k"
    DEBUG = False
    APP_NAME = "test"
    APP_STAGE = "test"


_cfg_mod.Config = _StubConfig
sys.modules["genericsuite.config.config"] = _cfg_mod

_bson = MagicMock()
_bson.json_util = MagicMock()
_bson.json_util.ObjectId = str
sys.modules["bson"] = _bson
sys.modules["bson.json_util"] = _bson.json_util

from genericsuite.util.utilities import (
    get_default_resultset,
    error_resultset,
    email_verification,
    check_email,
)


# ---- get_default_resultset ----

def test_get_default_resultset_has_required_keys():
    rs = get_default_resultset()
    assert "error" in rs
    assert "error_message" in rs
    assert "resultset" in rs


def test_get_default_resultset_error_is_false():
    rs = get_default_resultset()
    assert rs["error"] is False


def test_get_default_resultset_error_message_is_none():
    rs = get_default_resultset()
    assert rs["error_message"] is None


# ---- error_resultset ----

def test_error_resultset_sets_error_true():
    rs = error_resultset("something went wrong")
    assert rs["error"] is True


def test_error_resultset_includes_message():
    rs = error_resultset("bad input")
    assert "bad input" in rs["error_message"]


# ---- check_email ----

def test_check_email_valid():
    assert check_email("user@example.com") is not None


def test_check_email_invalid():
    assert check_email("not-an-email") is None


# ---- email_verification ----

def test_email_verification_valid():
    data = {"email": "good@example.com"}
    result = email_verification(data, ["email"])
    assert result["error_message"] is None


def test_email_verification_invalid_format():
    data = {"email": "bad-email"}
    result = email_verification(data, ["email"])
    assert result["error_message"] is not None


def test_email_verification_missing_field():
    data = {}
    result = email_verification(data, ["email"])
    assert result["error_message"] is not None


# ---- Additional imports from the same module ----

from genericsuite.util.utilities import (
    get_file_size,
    sort_list_of_dicts,
    get_id_as_string,
    get_default_value,
    get_mime_type,
    get_valid_extensions,
    get_url_query_args,
    get_file_extension,
    get_last_url_element,
    is_an_url,
    interpret_any,
    is_under_test,
    get_non_empty_value,
    get_standard_base_exception_msg,
    deduce_filename_from_url,
)


# ---- get_file_size ----

def test_get_file_size_bytes():
    assert get_file_size(500, "bytes") == "500 bytes"


def test_get_file_size_kb():
    result = get_file_size(1024, "kb")
    assert "1.00 Kb" in result


def test_get_file_size_mb_default():
    result = get_file_size(1024 * 1024)
    assert "1.00 Mb" in result


def test_get_file_size_gb():
    result = get_file_size(1024 ** 3, "gb")
    assert "1.00 Gb" in result


# ---- sort_list_of_dicts ----

def test_sort_list_of_dicts_asc():
    data = [{"name": "Charlie"}, {"name": "Alice"}, {"name": "Bob"}]
    result = sort_list_of_dicts(data, "name", "asc")
    assert [d["name"] for d in result] == ["Alice", "Bob", "Charlie"]


def test_sort_list_of_dicts_desc():
    data = [{"name": "Alice"}, {"name": "Charlie"}, {"name": "Bob"}]
    result = sort_list_of_dicts(data, "name", "desc")
    assert result[0]["name"] == "Charlie"


def test_sort_list_of_dicts_empty():
    assert sort_list_of_dicts([], "name", "asc") == []


# ---- get_id_as_string ----

def test_get_id_as_string_plain_string():
    row = {"_id": "abc123"}
    assert get_id_as_string(row) == "abc123"


def test_get_id_as_string_oid_dict():
    row = {"_id": {"$oid": "507f1f77bcf86cd799439011"}}
    assert get_id_as_string(row) == "507f1f77bcf86cd799439011"


# ---- get_default_value ----

def test_get_default_value_present():
    assert get_default_value("key", {"key": "val"}, "default") == "val"


def test_get_default_value_missing():
    assert get_default_value("missing", {}, "fallback") == "fallback"


# ---- get_file_extension ----

def test_get_file_extension_normal():
    assert get_file_extension("photo.jpg") == "jpg"


def test_get_file_extension_no_extension():
    assert get_file_extension("noextension") == ""


def test_get_file_extension_none():
    assert get_file_extension(None) == ""


def test_get_file_extension_dotfile():
    assert get_file_extension("archive.tar.gz") == "gz"


# ---- get_last_url_element ----

def test_get_last_url_element():
    assert get_last_url_element("https://example.com/path/to/file.jpg") == "file.jpg"


def test_get_last_url_element_root():
    assert get_last_url_element("https://example.com/") == ""


# ---- is_an_url ----

def test_is_an_url_http():
    assert is_an_url("http://example.com") is True


def test_is_an_url_https():
    assert is_an_url("https://example.com/file") is True


def test_is_an_url_local_path():
    assert is_an_url("/local/path/file.txt") is False


def test_is_an_url_ftp():
    assert is_an_url("ftp://files.example.com") is True


# ---- get_mime_type ----

def test_get_mime_type_jpg():
    result = get_mime_type("photo.jpg")
    assert "image" in result


def test_get_mime_type_png():
    result = get_mime_type("image.png")
    assert "image" in result


def test_get_mime_type_unknown_extension():
    result = get_mime_type("file.xyz_unknown_gs")
    assert result == "application/octet-stream"


def test_get_mime_type_mp3():
    result = get_mime_type("audio.mp3")
    assert "audio" in result


# ---- get_valid_extensions ----

def test_get_valid_extensions_image():
    exts = get_valid_extensions("image")
    assert "jpg" in exts
    assert "png" in exts


def test_get_valid_extensions_unknown_type():
    assert get_valid_extensions("nonexistent_type") == []


def test_get_valid_extensions_all():
    exts = get_valid_extensions()
    assert len(exts) > 5
    assert "jpg" in exts
    assert "mp3" in exts


# ---- get_url_query_args ----

def test_get_url_query_args_with_params():
    result = get_url_query_args("https://example.com/path?a=1&b=2")
    assert result["a"] == "1"
    assert result["b"] == "2"


def test_get_url_query_args_no_params():
    result = get_url_query_args("no-query-string")
    assert isinstance(result, dict)


# ---- interpret_any ----

def test_interpret_any_string():
    assert interpret_any("hello") == "hello"


def test_interpret_any_dict():
    result = interpret_any({"a": "foo", "b": "bar"})
    assert "foo" in result
    assert "bar" in result


def test_interpret_any_list():
    result = interpret_any(["x", "y"])
    assert "x" in result
    assert "y" in result


def test_interpret_any_int():
    assert interpret_any(42) == "42"


# ---- is_under_test ----

def test_is_under_test_returns_bool():
    result = is_under_test()
    assert isinstance(result, bool)


def test_is_under_test_true_during_pytest():
    import os
    # PYTEST_CURRENT_TEST is set when running under pytest
    assert is_under_test() is True


# ---- get_non_empty_value ----

def test_get_non_empty_value_set():
    import os
    os.environ["_GS_TEST_VAR"] = "hello"
    assert get_non_empty_value("_GS_TEST_VAR") == "hello"
    del os.environ["_GS_TEST_VAR"]


def test_get_non_empty_value_missing_returns_default():
    assert get_non_empty_value("_GS_MISSING_VAR_TEST", "fallback") == "fallback"


# ---- deduce_filename_from_url ----

def test_deduce_filename_from_url_direct():
    url = "https://example.com/assets/photo.jpg"
    result = deduce_filename_from_url(url, "image")
    assert result == "photo.jpg"


def test_deduce_filename_from_url_no_extension():
    url = "https://example.com/api/data"
    result = deduce_filename_from_url(url)
    assert result == ""
