"""
Tests for genericsuite/util/app_context.py — ParamsFile safe filename logic.
"""
import sys
import os
from unittest.mock import MagicMock, patch


def _setup_and_import_paramsfile():
    """Remove cached module and reimport ParamsFile with fresh mocks."""
    for mod in list(sys.modules):
        if "genericsuite.util.app_context" in mod:
            del sys.modules[mod]

    sys.modules["genericsuite.util.framework_abs_layer"] = MagicMock()
    sys.modules["genericsuite.util.app_logger"] = MagicMock()
    sys.modules["genericsuite.util.generic_db_helpers"] = MagicMock()
    sys.modules["genericsuite.util.jwt"] = MagicMock()

    _util_mock = MagicMock()
    _util_mock.get_default_resultset.return_value = {
        "error": False, "error_message": None, "resultset": {}, "totalPages": None
    }
    _util_mock.get_id_as_string = str
    sys.modules["genericsuite.util.utilities"] = _util_mock

    _secrets_mock = MagicMock()
    _secrets_mock.get_secrets_cache_filename.return_value = "/tmp/s_ec_test"
    sys.modules["genericsuite.config.config_secrets"] = _secrets_mock

    _const_mock = MagicMock()
    _const_mock.get_constant.return_value = {}
    sys.modules["genericsuite.constants.const_tables"] = _const_mock

    _curr_user_mock = MagicMock()
    _curr_user_mock.get_curr_user_data = MagicMock()
    _curr_user_mock.get_curr_user_id = MagicMock(return_value="test_user_id")
    _curr_user_mock.NON_AUTH_REQUEST_USER_ID = "[N/A/R]"
    sys.modules["genericsuite.util.current_user_data"] = _curr_user_mock

    env_patch = {
        "PARAMS_FILE_ENABLED": "0",
        "TEMP_DIR": "/tmp",
        "PARAMS_FILE_USER_FILENAME_TEMPLATE": "params_[user_id].json",
        "PARAMS_FILE_GENERAL_FILENAME": "params_GENERAL.json",
    }
    with patch.dict(os.environ, env_patch):
        from genericsuite.util.app_context import ParamsFile
        return ParamsFile


def test_get_params_filename_with_valid_objectid():
    ParamsFile = _setup_and_import_paramsfile()
    pf = ParamsFile("507f1f77bcf86cd799439011")
    filename = pf.get_params_filename()
    assert filename is not None
    assert "507f1f77bcf86cd799439011" in filename


def test_get_params_filename_strips_path_traversal_chars():
    ParamsFile = _setup_and_import_paramsfile()
    pf = ParamsFile("../etc/passwd")
    filename = pf.get_params_filename()
    assert "../" not in filename


def test_get_params_filename_strips_null_bytes():
    ParamsFile = _setup_and_import_paramsfile()
    pf = ParamsFile("abc\x00def")
    filename = pf.get_params_filename()
    assert "\x00" not in filename


def test_get_params_filename_strips_slashes():
    ParamsFile = _setup_and_import_paramsfile()
    pf = ParamsFile("user/id/with/slashes")
    filename = pf.get_params_filename()
    import os as _os
    basename = _os.path.basename(filename)
    assert "/" not in basename


def test_safe_params_path_keeps_file_under_temp_dir():
    ParamsFile = _setup_and_import_paramsfile()
    pf = ParamsFile("507f1f77bcf86cd799439011")
    safe = pf._safe_params_path("/tmp/params_507f1f77bcf86cd799439011.json")
    assert safe == os.path.realpath("/tmp/params_507f1f77bcf86cd799439011.json")
    assert safe.startswith(os.path.realpath("/tmp") + os.sep)


def test_safe_params_path_strips_directory_components():
    ParamsFile = _setup_and_import_paramsfile()
    pf = ParamsFile("test_user")
    safe = pf._safe_params_path("/etc/passwd")
    assert safe == os.path.realpath("/tmp/passwd")
    assert not safe.startswith(os.path.realpath("/etc"))


def test_safe_params_path_rejects_empty_basename():
    ParamsFile = _setup_and_import_paramsfile()
    pf = ParamsFile("test_user")
    try:
        pf._safe_params_path("")
        assert False, "Expected ValueError for empty filename"
    except ValueError as exc:
        assert "Invalid params filename" in str(exc)


def test_safe_params_path_rejects_dot_and_dotdot():
    ParamsFile = _setup_and_import_paramsfile()
    pf = ParamsFile("test_user")
    for bad in (".", ".."):
        try:
            pf._safe_params_path(bad)
            assert False, f"Expected ValueError for {bad!r}"
        except ValueError as exc:
            assert "Invalid params filename" in str(exc)


def test_save_params_file_writes_only_under_temp_dir(tmp_path):
    """save_params_file must not write outside TEMP_DIR even if given /etc/...."""
    ParamsFile = _setup_and_import_paramsfile()
    outside = tmp_path / "outside.json"
    with patch.dict(os.environ, {
        "PARAMS_FILE_ENABLED": "1",
        "USER_PARAMS_FILE_ENABLED": "1",
        "TEMP_DIR": "/tmp",
    }):
        # Re-import so module-level TEMP_DIR / flags pick up env if needed
        for mod in list(sys.modules):
            if "genericsuite.util.app_context" in mod:
                del sys.modules[mod]
        from genericsuite.util.app_context import ParamsFile as PF
        pf = PF("test_user")
        # Force flags on the instance path by patching module attrs
        import genericsuite.util.app_context as ac
        with patch.object(ac, "USER_PARAMS_FILE_ENABLED", "1"), \
             patch.object(ac, "PARAMS_FILE_ENABLED", "1"), \
             patch.object(ac, "TEMP_DIR", "/tmp"):
            result = pf.save_params_file(str(outside), {"_id": "test_user", "x": 1})
    assert result["error"] is False
    assert not outside.exists()
    expected = os.path.realpath(os.path.join("/tmp", outside.name))
    assert os.path.exists(expected)
    os.remove(expected)


def test_load_params_file_disabled():
    """When PARAMS_FILE_ENABLED=0 load returns found=False."""
    ParamsFile = _setup_and_import_paramsfile()
    with patch.dict(os.environ, {"PARAMS_FILE_ENABLED": "0"}):
        pf = ParamsFile("test_user")
        result = pf.load_params_file("/tmp/some_file.json")
    assert result["found"] is False


def test_load_params_file_nonexistent():
    """Loading a file that does not exist returns found=False."""
    ParamsFile = _setup_and_import_paramsfile()
    with patch.dict(os.environ, {"PARAMS_FILE_ENABLED": "1"}):
        pf = ParamsFile("test_user")
        result = pf.load_params_file("/tmp/__nonexistent_gs_test__.json")
    assert result["found"] is False
