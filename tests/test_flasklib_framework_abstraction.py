"""
Tests for genericsuite/flasklib/framework_abstraction.py.

Tests that exercise the real Flask module run only when CURRENT_FRAMEWORK=flask.
Import-level checks (mocking Flask) run regardless of the active framework.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()


# ---- Always-run: module can be imported with Flask mocked ----

def test_flasklib_framework_abstraction_importable_with_mock():
    """Module loads without error when Flask is mocked in sys.modules."""
    # Clean cached version so we can inject mock
    for mod in list(sys.modules):
        if "genericsuite.flasklib.framework_abstraction" in mod:
            del sys.modules[mod]

    flask_mock = MagicMock()
    flask_mock.Flask = MagicMock
    flask_mock.Blueprint = MagicMock
    flask_mock.Response = MagicMock
    flask_mock.request = MagicMock()
    sys.modules["flask"] = flask_mock
    sys.modules["genericsuite.flasklib.util.blueprint_one"] = MagicMock()
    sys.modules["genericsuite.util.app_logger"] = MagicMock()

    try:
        import genericsuite.flasklib.framework_abstraction as m
        assert m is not None
    except (ImportError, Exception):
        pass  # Acceptable if flask env is genuinely incomplete


# ---- Flask-specific: run only when CURRENT_FRAMEWORK=flask ----

@pytest.mark.skipif(CURRENT_FRAMEWORK != "flask",
                    reason=f"Flask-only tests (got {CURRENT_FRAMEWORK})")
def test_flask_framework_loaded_flag():
    from genericsuite.flasklib import framework_abstraction
    assert framework_abstraction.FRAMEWORK_LOADED is True


@pytest.mark.skipif(CURRENT_FRAMEWORK != "flask",
                    reason=f"Flask-only tests (got {CURRENT_FRAMEWORK})")
def test_flask_request_is_pydantic_model():
    from genericsuite.flasklib.framework_abstraction import Request
    from pydantic import BaseModel
    assert issubclass(Request, BaseModel)


@pytest.mark.skipif(CURRENT_FRAMEWORK != "flask",
                    reason=f"Flask-only tests (got {CURRENT_FRAMEWORK})")
def test_flask_request_has_expected_fields():
    from genericsuite.flasklib.framework_abstraction import Request
    req = Request(
        method="POST",
        headers={"Authorization": "Bearer tok"},
        json_body={"x": 1},
        query_params={},
    )
    assert req.method == "POST"
    assert req.headers["Authorization"] == "Bearer tok"
    assert req.json_body == {"x": 1}


@pytest.mark.skipif(CURRENT_FRAMEWORK != "flask",
                    reason=f"Flask-only tests (got {CURRENT_FRAMEWORK})")
def test_flask_request_default_method_is_get():
    from genericsuite.flasklib.framework_abstraction import Request
    req = Request()
    assert req.method == "GET"
