"""
Tests for chalicelib/endpoints/*.py — import coverage via mocked Chalice.

Importing these modules exercises all module-level code:
  bp = BlueprintOne(__name__)
  @bp.route(...)
  async def endpoint(...):  ← def line is covered

Tests run only when CURRENT_FRAMEWORK=chalice.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()

pytestmark = pytest.mark.skipif(
    CURRENT_FRAMEWORK != "chalice",
    reason="Chalice endpoint import tests only run with CURRENT_FRAMEWORK=chalice",
)


def _setup_chalice_mocks():
    """Set up the minimal chalice + genericsuite mocks for endpoint imports."""
    chalice_mock = MagicMock()
    chalice_mock.Blueprint = type("Blueprint", (), {
        "__init__": lambda self, *a, **kw: None,
        "route": lambda self, *a, **kw: (lambda f: f),
        "_create_registration_function": MagicMock(return_value=MagicMock()),
    })
    chalice_mock.app = MagicMock()
    chalice_mock.app.Blueprint = chalice_mock.Blueprint
    chalice_mock.app.Request = MagicMock
    sys.modules.setdefault("chalice", chalice_mock)
    sys.modules.setdefault("chalice.app", chalice_mock.app)
    # Mock genericsuite.util.framework_abs_layer so that importing endpoints
    # gets a MagicMock for BlueprintOne, Response, etc.
    sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.util.jwt", MagicMock())
    sys.modules.setdefault("genericsuite.chalicelib.util.blueprint_one", MagicMock())


# ---- logs ----

def test_chalicelib_logs_endpoint_importable():
    _setup_chalice_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.chalicelib.endpoints.logs":
            del sys.modules[mod]
    import genericsuite.chalicelib.endpoints.logs as m
    assert m.bp is not None


def test_chalicelib_logs_creation_is_callable():
    _setup_chalice_mocks()
    import genericsuite.chalicelib.endpoints.logs as m
    assert callable(m.logs_creation)


# ---- menu_options ----

def test_chalicelib_menu_options_endpoint_importable():
    _setup_chalice_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.chalicelib.endpoints.menu_options":
            del sys.modules[mod]
    import genericsuite.chalicelib.endpoints.menu_options as m
    assert m.bp is not None


def test_chalicelib_menu_options_get_is_callable():
    _setup_chalice_mocks()
    import genericsuite.chalicelib.endpoints.menu_options as m
    assert callable(m.menu_options_get)


# ---- users ----

def test_chalicelib_users_endpoint_importable():
    _setup_chalice_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.chalicelib.endpoints.users":
            del sys.modules[mod]
    import genericsuite.chalicelib.endpoints.users as m
    assert m.bp is not None


def test_chalicelib_users_login_is_callable():
    _setup_chalice_mocks()
    import genericsuite.chalicelib.endpoints.users as m
    assert callable(m.login_user)


def test_chalicelib_users_test_connection_is_callable():
    _setup_chalice_mocks()
    import genericsuite.chalicelib.endpoints.users as m
    assert callable(m.test_connection_handler)


# ---- storage_retrieval ----

def test_chalicelib_storage_retrieval_importable():
    _setup_chalice_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.chalicelib.endpoints.storage_retrieval":
            del sys.modules[mod]
    import genericsuite.chalicelib.endpoints.storage_retrieval as m
    assert m.bp is not None
