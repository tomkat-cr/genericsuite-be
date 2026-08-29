"""
Tests for genericsuite/config/config_from_db.py — DB-backed config.
"""
import os
import sys
from unittest.mock import MagicMock, patch


def _setup_mocks():
    """Install sys.modules stubs so config_from_db can be imported cleanly."""
    for mod in list(sys.modules):
        if "genericsuite.config.config_from_db" in mod:
            del sys.modules[mod]

    mock_fw = MagicMock()
    mock_fw.Request = MagicMock
    mock_fw.Response = MagicMock
    sys.modules.setdefault("genericsuite.util.framework_abs_layer", mock_fw)

    mock_logger = MagicMock()
    mock_logger.log_debug = MagicMock()
    mock_logger.log_error = MagicMock()
    sys.modules.setdefault("genericsuite.util.app_logger", mock_logger)

    mock_app_ctx = MagicMock()
    mock_app_ctx.NON_AUTH_REQUEST_USER_ID = "[N/A/R]"
    mock_app_ctx.PARAMS_FILE_ENABLED = "0"
    mock_app_ctx.PARAMS_FILE_GENERAL_FILENAME = "params_GENERAL.json"
    sys.modules.setdefault("genericsuite.util.app_context", mock_app_ctx)

    mock_jwt = MagicMock()
    sys.modules.setdefault("genericsuite.util.jwt", mock_jwt)

    mock_utilities = MagicMock()
    mock_utilities.get_default_resultset.return_value = {
        "error": False, "error_message": None,
        "resultset": {}, "totalPages": None,
    }
    sys.modules.setdefault("genericsuite.util.utilities", mock_utilities)


def test_get_general_config_disabled():
    """When USE_DB_PARAMS=0 returns an empty resultset without DB call."""
    _setup_mocks()
    with patch.dict(os.environ, {"USE_DB_PARAMS": "0"}):
        from genericsuite.config.config_from_db import get_general_config
        app_context = MagicMock()
        result = get_general_config(app_context)
    assert result["error"] is False


def test_get_users_config_returns_dict():
    """get_users_config always returns resultset as dict."""
    _setup_mocks()
    from genericsuite.config.config_from_db import get_users_config
    app_context = MagicMock()
    app_context.get_user_data.return_value = {
        "users_config": [{"config_name": "k", "config_value": "v"}]
    }
    result = get_users_config(app_context)
    assert result["error"] is False
    assert isinstance(result["resultset"], dict)
