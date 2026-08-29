"""
Tests for genericsuite/flasklib/util/jwt.py — token_required decorator.

Flask and flask-related modules are mocked since Flask is not a hard
dependency in the dev environment.

Tests run only when CURRENT_FRAMEWORK=flask.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()

pytestmark = pytest.mark.skipif(
    CURRENT_FRAMEWORK != "flask",
    reason="Flask JWT decorator tests only run with CURRENT_FRAMEWORK=flask",
)


def _import_token_required():
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

    for mod in list(sys.modules):
        if mod == "genericsuite.flasklib.util.jwt":
            del sys.modules[mod]

    from genericsuite.flasklib.util.jwt import token_required
    from genericsuite.util.jwt import AuthorizedRequest
    return token_required, AuthorizedRequest


# ---- token_required decorator ----

def test_token_required_returns_callable():
    token_required, _ = _import_token_required()

    @token_required
    def my_view(request, **kwargs):
        return "ok"

    assert callable(my_view)


def test_token_required_passes_authorized_request_to_function():
    token_required, AuthorizedRequest = _import_token_required()

    authorized = MagicMock(spec=AuthorizedRequest)
    results = []

    @token_required
    def my_view(request, **kwargs):
        results.append(request)
        return "ok"

    with patch("genericsuite.flasklib.util.jwt.get_general_authorized_request",
               return_value=authorized):
        result = my_view(MagicMock())

    assert result == "ok"
    assert results[0] is authorized


def test_token_required_returns_error_response_on_invalid_token():
    token_required, AuthorizedRequest = _import_token_required()

    error_response = MagicMock()

    @token_required
    def my_view(request, **kwargs):
        return "should not reach"

    with patch("genericsuite.flasklib.util.jwt.get_general_authorized_request",
               return_value=error_response):
        result = my_view(MagicMock())

    assert result is error_response


def test_token_required_preserves_function_name():
    token_required, _ = _import_token_required()

    @token_required
    def my_special_view(request, **kwargs):
        return "ok"

    assert my_special_view.__name__ == "my_special_view"


def test_token_required_passes_kwargs():
    token_required, AuthorizedRequest = _import_token_required()

    authorized = MagicMock(spec=AuthorizedRequest)
    captured_kwargs = {}

    @token_required
    def my_view(request, **kwargs):
        captured_kwargs.update(kwargs)
        return "ok"

    with patch("genericsuite.flasklib.util.jwt.get_general_authorized_request",
               return_value=authorized):
        my_view(MagicMock(), extra_param="hello")

    assert captured_kwargs.get("extra_param") == "hello"
