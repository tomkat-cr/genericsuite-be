"""
Tests for:
  genericsuite/fastapilib/util/dependencies.py — build_request()
  genericsuite/fastapilib/util/blueprint_one.py — BlueprintOne helper methods

These tests run only when CURRENT_FRAMEWORK=fastapi (fastapi is installed
as a dependency so the modules import without issues).
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()

pytestmark = pytest.mark.skipif(
    CURRENT_FRAMEWORK != "fastapi",
    reason="FastAPI deps/blueprint tests only run with CURRENT_FRAMEWORK=fastapi",
)


# ---------------------------------------------------------------------------
# _AuthorizedRequest is defined at module level so every call to
# _setup_deps_mocks() installs the SAME class object as jwt.AuthorizedRequest.
# build_request() and the test body both see the same class, so isinstance()
# works correctly.
# ---------------------------------------------------------------------------

class _AuthorizedRequest:
    """Minimal AuthorizedRequest stand-in for build_request tests."""
    def __init__(self, method="get", query_params=None, json_body=None,
                 headers=None, user=None, **kwargs):
        self.method = method
        self.query_params = query_params if query_params is not None else {}
        self.json_body = json_body if json_body is not None else {}
        self.headers = headers if headers is not None else {}
        self.user = user


def _setup_deps_mocks():
    """
    Inject the mocks that dependencies.py needs to import cleanly.

    jwt is always replaced with our controlled mock so that:
      • The real jwt.py (which requires Pydantic + a live Config) is never
        imported in this unit-test context.
      • AuthorizedRequest is our plain _AuthorizedRequest class, making
        isinstance() assertions predictable.

    genericsuite.fastapilib.framework_abstraction is NOT mocked so that the
    real Pydantic Request class is used. This avoids corrupting the module
    cache for later tests (test_fastapilib_framework_abstraction.py and
    test_util_framework_abs_layer.py) that need the real implementation.
    """
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

    if "genericsuite.util.framework_abs_layer" not in sys.modules:
        fw_mock = MagicMock()
        fw_mock.Request = MagicMock  # CLASS, not instance
        fw_mock.Response = MagicMock
        sys.modules["genericsuite.util.framework_abs_layer"] = fw_mock

    # Always replace jwt with our stub so isinstance() tests are reliable.
    jwt_mock = MagicMock()
    jwt_mock.AuthorizedRequest = _AuthorizedRequest
    jwt_mock.AuthTokenPayload = MagicMock
    jwt_mock.get_general_authorized_request = MagicMock()
    sys.modules["genericsuite.util.jwt"] = jwt_mock


def _import_deps():
    _setup_deps_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.fastapilib.util.dependencies":
            del sys.modules[mod]
    from genericsuite.fastapilib.util.dependencies import build_request
    return build_request


def _import_blueprint():
    for mod in list(sys.modules):
        if mod == "genericsuite.fastapilib.util.blueprint_one":
            del sys.modules[mod]
    from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
    return BlueprintOne


# ============================================================
# build_request
# ============================================================

def test_build_request_no_args_creates_request():
    build_request = _import_deps()
    req = build_request()
    assert req is not None


def test_build_request_with_method():
    build_request = _import_deps()
    req = build_request(method="POST")
    assert req.method.upper() == "POST"


def test_build_request_with_query_params():
    build_request = _import_deps()
    req = build_request(query_params={"page": "1", "limit": "10"})
    assert req.query_params.get("page") == "1"


def test_build_request_filters_none_query_params():
    build_request = _import_deps()
    req = build_request(query_params={"page": "1", "limit": None})
    assert "limit" not in req.query_params


def test_build_request_preserves_none_with_flag():
    build_request = _import_deps()
    req = build_request(query_params={"page": "1", "limit": None}, preserve_nones=True)
    assert "limit" in req.query_params


def test_build_request_with_json_body():
    build_request = _import_deps()
    req = build_request(json_body={"key": "value"})
    assert req.json_body.get("key") == "value"


def test_build_request_with_headers():
    build_request = _import_deps()
    req = build_request(headers={"x-custom": "abc"})
    assert req.headers.get("x-custom") == "abc"


def test_build_request_token_header_becomes_bearer():
    build_request = _import_deps()
    req = build_request(headers={"token": "mytoken123"})
    assert "Authorization" in req.headers
    assert req.headers["Authorization"] == "Bearer mytoken123"
    assert "token" not in req.headers


def test_build_request_current_user_creates_authorized_request():
    build_request = _import_deps()
    from genericsuite.util.jwt import AuthorizedRequest
    user_mock = MagicMock()
    req = build_request(headers={"current_user": user_mock})
    assert isinstance(req, AuthorizedRequest)


def test_build_request_no_current_user_creates_plain_request():
    build_request = _import_deps()
    from genericsuite.util.jwt import AuthorizedRequest
    req = build_request(headers={"x-other": "value"})
    assert not isinstance(req, AuthorizedRequest)


def test_build_request_empty_headers():
    build_request = _import_deps()
    req = build_request(headers={})
    assert req.headers == {}


# ============================================================
# BlueprintOne (FastAPI variant)
# ============================================================

def test_blueprint_one_init_no_args():
    BlueprintOne = _import_blueprint()
    bp = BlueprintOne()
    assert bp is not None


def test_blueprint_one_has_name_attribute():
    BlueprintOne = _import_blueprint()
    bp = BlueprintOne()
    # name defaults to "NoName" unless set via positional arg passed to __init__
    assert hasattr(bp, "name")


def test_blueprint_one_get_current_app_initially_none():
    BlueprintOne = _import_blueprint()
    bp = BlueprintOne()
    assert bp.get_current_app() is None


def test_blueprint_one_set_current_app():
    BlueprintOne = _import_blueprint()
    bp = BlueprintOne()
    mock_app = MagicMock()
    result = bp.set_current_app(mock_app)
    assert result is mock_app
    assert bp.get_current_app() is mock_app


def test_blueprint_one_get_current_request_initially_none():
    BlueprintOne = _import_blueprint()
    bp = BlueprintOne()
    assert bp.get_current_request() is None


def test_blueprint_one_get_current_fa_request_initially_none():
    BlueprintOne = _import_blueprint()
    bp = BlueprintOne()
    assert bp.get_current_fa_request() is None


def test_blueprint_one_to_original_event_returns_empty_dict():
    BlueprintOne = _import_blueprint()
    bp = BlueprintOne()
    result = bp.to_original_event()
    assert result == {}


def test_blueprint_one_name_defaults_to_noname():
    BlueprintOne = _import_blueprint()
    bp = BlueprintOne()
    assert bp.name == "NoName"
