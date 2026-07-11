"""
Tests for flasklib/endpoints/*.py — import coverage via mocked Flask.

Importing these modules exercises all module-level code:
  settings = Config()
  bp = BlueprintOne("logs", __name__, url_prefix=...)
  @bp.route(...)
  def endpoint(...):  ← def line is covered

Tests run only when CURRENT_FRAMEWORK=flask.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()

pytestmark = pytest.mark.skipif(
    CURRENT_FRAMEWORK != "flask",
    reason="Flask endpoint import tests only run with CURRENT_FRAMEWORK=flask",
)


def _setup_flask_mocks():
    """Set up flask + blueprint mocks for endpoint imports."""
    sys.modules.setdefault(
        "genericsuite.util.framework_abs_layer", MagicMock())
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.util.jwt", MagicMock())
    sys.modules.setdefault("genericsuite.util.app_context", MagicMock())
    sys.modules.setdefault("genericsuite.util.security", MagicMock())
    # Mock flasklib-specific utilities so endpoints can import without
    # real Flask
    sys.modules.setdefault(
        "genericsuite.flasklib.util.blueprint_one", MagicMock())
    sys.modules.setdefault("genericsuite.flasklib.util.jwt", MagicMock())
    sys.modules.setdefault(
        "genericsuite.flasklib.framework_abstraction", MagicMock())
    # logs.py imports get_flask_limiter → flask_limiter → flask.wrappers.
    # Earlier tests (create_app_cors / framework_abstraction) leave
    # sys.modules["flask"] as a MagicMock, so the real flask_limiter
    # import fails with
    # "No module named 'flask.wrappers'; 'flask' is not a package".
    sys.modules.setdefault("genericsuite.flasklib.util.limiter", MagicMock())
    # test_create_app_cors.py installs MagicMock for
    # genericsuite.flasklib.endpoints
    # (the package) via setdefault; Python refuses to treat a MagicMock as
    # a package namespace, so sub-module imports fail with "not a package".
    # Evict it.
    for _mod in list(sys.modules):
        if _mod == "genericsuite.flasklib.endpoints" or \
                _mod.startswith("genericsuite.flasklib.endpoints."):
            del sys.modules[_mod]


# ---- logs ----

def test_flasklib_logs_endpoint_importable():
    _setup_flask_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.flasklib.endpoints.logs":
            del sys.modules[mod]
    import genericsuite.flasklib.endpoints.logs as m
    assert m.bp is not None


def test_flasklib_logs_creation_is_callable():
    _setup_flask_mocks()
    import genericsuite.flasklib.endpoints.logs as m
    assert callable(m.logs_creation)


# ---- menu_options ----

def test_flasklib_menu_options_endpoint_importable():
    _setup_flask_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.flasklib.endpoints.menu_options":
            del sys.modules[mod]
    import genericsuite.flasklib.endpoints.menu_options as m
    assert m.bp is not None


def test_flasklib_menu_options_get_is_callable():
    _setup_flask_mocks()
    import genericsuite.flasklib.endpoints.menu_options as m
    assert callable(m.menu_options_get)


# ---- users ----

def test_flasklib_users_endpoint_importable():
    _setup_flask_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.flasklib.endpoints.users":
            del sys.modules[mod]
    import genericsuite.flasklib.endpoints.users as m
    assert m.bp is not None


def test_flasklib_users_login_is_callable():
    _setup_flask_mocks()
    import genericsuite.flasklib.endpoints.users as m
    assert callable(m.login_user)


def test_flasklib_users_test_connection_is_callable():
    _setup_flask_mocks()
    import genericsuite.flasklib.endpoints.users as m
    assert callable(m.test_connection_handler)


# ---- storage_retrieval ----

def test_flasklib_storage_retrieval_importable():
    _setup_flask_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.flasklib.endpoints.storage_retrieval":
            del sys.modules[mod]
    import genericsuite.flasklib.endpoints.storage_retrieval as m
    assert m.bp is not None
