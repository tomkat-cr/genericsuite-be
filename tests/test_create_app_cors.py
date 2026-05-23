"""
Tests for the set_cors_config() helpers in each framework's create_app module.

Only the pure helper functions are tested (not create_app itself, which
requires a live framework instance). Framework-specific tests are gated by
CURRENT_FRAMEWORK.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()


# ============================================================
# Flask: set_cors_config — returns a plain dict (always works)
# ============================================================

def _import_flask_create_app():
    """Import flasklib/util/create_app.py with Flask mocked."""
    # Mock entire flask stack so the module imports without flask installed
    flask_mock = MagicMock()
    flask_mock.Flask = type("Flask", (), {"__init__": lambda self, *a, **kw: None})
    sys.modules.setdefault("flask", flask_mock)
    sys.modules.setdefault("flask_cors", MagicMock())
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
    sys.modules.setdefault("genericsuite.flasklib.util.blueprint_one", MagicMock())
    sys.modules.setdefault("genericsuite.flasklib.util.generic_endpoint_builder", MagicMock())
    sys.modules.setdefault("genericsuite.flasklib.endpoints", MagicMock())
    sys.modules.setdefault("genericsuite.flasklib.endpoints.users", MagicMock())
    sys.modules.setdefault("genericsuite.flasklib.endpoints.menu_options", MagicMock())
    sys.modules.setdefault("genericsuite.flasklib.endpoints.storage_retrieval", MagicMock())
    sys.modules.setdefault("genericsuite.flasklib.endpoints.logs", MagicMock())
    sys.modules.setdefault("genericsuite.config.config_from_db", MagicMock())

    for mod in list(sys.modules):
        if mod == "genericsuite.flasklib.util.create_app":
            del sys.modules[mod]
    from genericsuite.flasklib.util.create_app import set_cors_config
    return set_cors_config


def _make_settings():
    cfg = MagicMock()
    cfg.CORS_ORIGIN = "https://app.example.com"
    cfg.API_VERSION = "v1"
    cfg.APP_VERSION = "1.0.0"
    cfg.APP_NAME = "test_app"
    cfg.HEADER_TOKEN_ENTRY_NAME = "x-access-token"
    cfg.DEBUG = False
    return cfg


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "flask",
    reason="Flask create_app tests only run with CURRENT_FRAMEWORK=flask",
)
def test_flask_set_cors_config_returns_dict():
    set_cors_config = _import_flask_create_app()
    result = set_cors_config(_make_settings())
    assert isinstance(result, dict)


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "flask",
    reason="Flask create_app tests only run with CURRENT_FRAMEWORK=flask",
)
def test_flask_set_cors_config_has_required_keys():
    set_cors_config = _import_flask_create_app()
    result = set_cors_config(_make_settings())
    assert "origins" in result
    assert "methods" in result
    assert "allow_headers" in result
    assert "expose_headers" in result


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "flask",
    reason="Flask create_app tests only run with CURRENT_FRAMEWORK=flask",
)
def test_flask_set_cors_config_uses_settings_origin():
    set_cors_config = _import_flask_create_app()
    settings = _make_settings()
    settings.CORS_ORIGIN = "http://localhost:3000"
    result = set_cors_config(settings)
    assert result["origins"] == "http://localhost:3000"


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "flask",
    reason="Flask create_app tests only run with CURRENT_FRAMEWORK=flask",
)
def test_flask_set_cors_config_includes_common_methods():
    set_cors_config = _import_flask_create_app()
    result = set_cors_config(_make_settings())
    assert "GET" in result["methods"]
    assert "POST" in result["methods"]
    assert "DELETE" in result["methods"]


# ============================================================
# Chalice: set_cors_config — creates a CORSConfig object
# ============================================================

def _import_chalice_create_app():
    """Import chalicelib/util/create_app.py with Chalice mocked."""
    # Use a MagicMock() INSTANCE (not the class) so assert_called_once() and
    # call_args work correctly — the class has no call-tracking state.
    cors_config_mock = MagicMock()
    chalice_mock = MagicMock()
    chalice_mock.Chalice = MagicMock
    chalice_mock.CORSConfig = cors_config_mock
    # Always update sys.modules["chalice"] (don't use setdefault) so that each
    # test gets a fresh, call-tracking CORSConfig mock and the just-imported
    # create_app module sees the same object that this function returns.
    sys.modules["chalice"] = chalice_mock
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.chalicelib.util.generic_endpoint_builder", MagicMock())
    sys.modules.setdefault("genericsuite.chalicelib.endpoints", MagicMock())
    sys.modules.setdefault("genericsuite.chalicelib.endpoints.users", MagicMock())
    sys.modules.setdefault("genericsuite.chalicelib.endpoints.menu_options", MagicMock())
    sys.modules.setdefault("genericsuite.chalicelib.endpoints.storage_retrieval", MagicMock())
    sys.modules.setdefault("genericsuite.chalicelib.endpoints.logs", MagicMock())
    sys.modules.setdefault("genericsuite.config.config_from_db", MagicMock())

    for mod in list(sys.modules):
        if mod == "genericsuite.chalicelib.util.create_app":
            del sys.modules[mod]
    from genericsuite.chalicelib.util.create_app import set_cors_config
    return set_cors_config, cors_config_mock


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "chalice",
    reason="Chalice create_app tests only run with CURRENT_FRAMEWORK=chalice",
)
def test_chalice_set_cors_config_calls_cors_config_class():
    set_cors_config, CORSConfigMock = _import_chalice_create_app()
    settings = _make_settings()
    set_cors_config(CORSConfigMock, settings)
    CORSConfigMock.assert_called_once()


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "chalice",
    reason="Chalice create_app tests only run with CURRENT_FRAMEWORK=chalice",
)
def test_chalice_set_cors_config_passes_allow_origin():
    set_cors_config, CORSConfigMock = _import_chalice_create_app()
    settings = _make_settings()
    settings.CORS_ORIGIN = "https://myapp.com"
    set_cors_config(CORSConfigMock, settings)
    call_kwargs = CORSConfigMock.call_args[1]
    assert call_kwargs.get("allow_origin") == "https://myapp.com"


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "chalice",
    reason="Chalice create_app tests only run with CURRENT_FRAMEWORK=chalice",
)
def test_chalice_set_cors_config_sets_credentials():
    set_cors_config, CORSConfigMock = _import_chalice_create_app()
    set_cors_config(CORSConfigMock, _make_settings())
    call_kwargs = CORSConfigMock.call_args[1]
    assert call_kwargs.get("allow_credentials") is True


# ============================================================
# FastAPI: set_cors_config — adds middleware to the app
# ============================================================

def _import_fastapi_create_app():
    """Import fastapilib/util/create_app.py with heavy endpoints mocked."""
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.fastapilib.util.generic_endpoint_builder", MagicMock())
    sys.modules.setdefault("genericsuite.fastapilib.endpoints", MagicMock())
    sys.modules.setdefault("genericsuite.fastapilib.endpoints.users", MagicMock())
    sys.modules.setdefault("genericsuite.fastapilib.endpoints.menu_options", MagicMock())
    sys.modules.setdefault("genericsuite.fastapilib.endpoints.storage_retrieval", MagicMock())
    sys.modules.setdefault("genericsuite.fastapilib.endpoints.api_documentation", MagicMock())
    sys.modules.setdefault("genericsuite.fastapilib.endpoints.logs", MagicMock())
    sys.modules.setdefault("genericsuite.config.config_from_db", MagicMock())

    for mod in list(sys.modules):
        if mod == "genericsuite.fastapilib.util.create_app":
            del sys.modules[mod]
    from genericsuite.fastapilib.util.create_app import set_cors_config, create_handler
    return set_cors_config, create_handler


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "fastapi",
    reason="FastAPI create_app tests only run with CURRENT_FRAMEWORK=fastapi",
)
def test_fastapi_set_cors_config_calls_add_middleware():
    set_cors_config, _ = _import_fastapi_create_app()
    mock_app = MagicMock()
    set_cors_config(mock_app, _make_settings())
    mock_app.add_middleware.assert_called_once()


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "fastapi",
    reason="FastAPI create_app tests only run with CURRENT_FRAMEWORK=fastapi",
)
def test_fastapi_set_cors_config_passes_origin():
    set_cors_config, _ = _import_fastapi_create_app()
    mock_app = MagicMock()
    settings = _make_settings()
    settings.CORS_ORIGIN = "https://myapp.com"
    set_cors_config(mock_app, settings)
    call_kwargs = mock_app.add_middleware.call_args[1]
    assert "https://myapp.com" in call_kwargs.get("allow_origins", [])


@pytest.mark.skipif(
    CURRENT_FRAMEWORK != "fastapi",
    reason="FastAPI create_app tests only run with CURRENT_FRAMEWORK=fastapi",
)
def test_fastapi_create_handler_returns_mangum_wrapper():
    _, create_handler = _import_fastapi_create_app()
    mock_app = MagicMock()
    handler = create_handler(mock_app)
    assert handler is not None
