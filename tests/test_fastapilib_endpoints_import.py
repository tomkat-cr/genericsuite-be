"""
Tests for fastapilib/endpoints/*.py — import coverage.

Just importing these modules exercises all module-level code:
  router = BlueprintOne()
  security = HTTPBasic()
  @router.post(...)
  async def endpoint(...):   ← def line is covered

Tests are skipped when CURRENT_FRAMEWORK != fastapi (but since fastapi
is always installed as a dep, the imports work in any framework mode).
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()

pytestmark = pytest.mark.skipif(
    CURRENT_FRAMEWORK != "fastapi",
    reason="FastAPI endpoint import tests only run with CURRENT_FRAMEWORK=fastapi",
)


def _ensure_fa_env():
    """Ensure framework_abs_layer is accessible (mocked if not real)."""
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    # Pre-mock jwt so it is never freshly imported when framework_abs_layer
    # may have a MagicMock instance as Request (jwt.py line 52/60 need a real type)
    sys.modules.setdefault("genericsuite.util.jwt", MagicMock())
    # Block the app_context → const_tables → Config chain.
    # test_models_users.py installs a _StubConfig at collection time that lacks
    # GIT_SUBMODULE_LOCAL_PATH; const_tables.py calls get_all_constants() at
    # module level, which blows up when Config is that stub.
    sys.modules.setdefault("genericsuite.util.app_context", MagicMock())
    # Block security.py which imports app_context (same chain).
    sys.modules.setdefault("genericsuite.util.security", MagicMock())
    # test_create_app_cors.py installs a MagicMock for genericsuite.fastapilib.endpoints
    # via setdefault (runs earlier alphabetically); Python refuses to treat a MagicMock as a
    # package namespace, so sub-module imports fail with "not a package". Evict it.
    for _mod in list(sys.modules):
        if _mod == "genericsuite.fastapilib.endpoints" or \
                _mod.startswith("genericsuite.fastapilib.endpoints."):
            del sys.modules[_mod]
    if "genericsuite.util.framework_abs_layer" not in sys.modules:
        fw_mock = MagicMock()
        fw_mock.Request = MagicMock  # CLASS, not instance
        sys.modules["genericsuite.util.framework_abs_layer"] = fw_mock
    # Always set Response = dict regardless of who created the mock first.
    # FastAPI route decorators validate the return-type annotation as a Pydantic
    # type; MagicMock fails that check, but dict is accepted unconditionally.
    sys.modules["genericsuite.util.framework_abs_layer"].Response = dict


# ---- logs ----

def test_fastapilib_logs_router_exists():
    _ensure_fa_env()
    for mod in list(sys.modules):
        if mod == "genericsuite.fastapilib.endpoints.logs":
            del sys.modules[mod]
    import genericsuite.fastapilib.endpoints.logs as m
    assert m.router is not None


def test_fastapilib_logs_creation_is_callable():
    _ensure_fa_env()
    import genericsuite.fastapilib.endpoints.logs as m
    assert callable(m.logs_creation)


# ---- menu_options ----

def test_fastapilib_menu_options_router_exists():
    _ensure_fa_env()
    for mod in list(sys.modules):
        if mod == "genericsuite.fastapilib.endpoints.menu_options":
            del sys.modules[mod]
    import genericsuite.fastapilib.endpoints.menu_options as m
    assert m.router is not None


def test_fastapilib_menu_options_get_is_callable():
    _ensure_fa_env()
    import genericsuite.fastapilib.endpoints.menu_options as m
    assert callable(m.menu_options_get)


# ---- users ----

def test_fastapilib_users_router_exists():
    _ensure_fa_env()
    for mod in list(sys.modules):
        if mod == "genericsuite.fastapilib.endpoints.users":
            del sys.modules[mod]
    import genericsuite.fastapilib.endpoints.users as m
    assert m.router is not None


def test_fastapilib_users_login_is_callable():
    _ensure_fa_env()
    import genericsuite.fastapilib.endpoints.users as m
    assert callable(m.login_user)


def test_fastapilib_users_security_object_exists():
    _ensure_fa_env()
    import genericsuite.fastapilib.endpoints.users as m
    assert m.security is not None


# ---- api_documentation ----

def test_fastapilib_api_documentation_router_exists():
    _ensure_fa_env()
    for mod in list(sys.modules):
        if mod == "genericsuite.fastapilib.endpoints.api_documentation":
            del sys.modules[mod]
    import genericsuite.fastapilib.endpoints.api_documentation as m
    assert m.router is not None


def test_fastapilib_save_openapi_json_is_callable():
    _ensure_fa_env()
    import genericsuite.fastapilib.endpoints.api_documentation as m
    assert callable(m.save_openapi_json)


def test_fastapilib_save_openapi_yaml_is_callable():
    _ensure_fa_env()
    import genericsuite.fastapilib.endpoints.api_documentation as m
    assert callable(m.save_openapi_yaml)


def test_fastapilib_save_openapi_json_writes_file(tmp_path):
    _ensure_fa_env()
    import genericsuite.fastapilib.endpoints.api_documentation as m
    fake_app = MagicMock()
    fake_app.openapi.return_value = {"openapi": "3.0.0", "paths": {}}
    out_path = str(tmp_path / "api.json")
    m.save_openapi_json(fake_app, out_path)
    assert os.path.exists(out_path)


def test_fastapilib_save_openapi_yaml_writes_file(tmp_path):
    _ensure_fa_env()
    import genericsuite.fastapilib.endpoints.api_documentation as m
    fake_app = MagicMock()
    fake_app.openapi.return_value = {"openapi": "3.0.0", "paths": {}}
    out_path = str(tmp_path / "api.yaml")
    m.save_openapi_yaml(fake_app, out_path)
    assert os.path.exists(out_path)


# ---- storage_retrieval ----

def test_fastapilib_storage_retrieval_router_exists():
    _ensure_fa_env()
    for mod in list(sys.modules):
        if mod == "genericsuite.fastapilib.endpoints.storage_retrieval":
            del sys.modules[mod]
    import genericsuite.fastapilib.endpoints.storage_retrieval as m
    assert m.router is not None
