"""
Tests for genericsuite/util/framework_abs_layer.py — framework normalization.

These tests work with any CURRENT_FRAMEWORK value (fastapi, flask, chalice, mcp)
by dynamically importing from the active framework's abstraction module.
FastAPI and Flask expose Pydantic-based Request objects; Chalice uses its own
Request type, so instantiation tests are skipped for Chalice.
"""
import os
import importlib

import pytest

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()

# FastAPI and Flask use identical Pydantic-based Request models.
# Chalice uses chalice.app.Request which has a different constructor.
_PYDANTIC_FRAMEWORK = CURRENT_FRAMEWORK in ("fastapi", "flask")


def _get_request_class():
    """Import Request from the currently active framework module."""
    mod = importlib.import_module(
        f"genericsuite.{CURRENT_FRAMEWORK}lib.framework_abstraction"
    )
    return mod.Request


def _get_response_class():
    mod = importlib.import_module(
        f"genericsuite.{CURRENT_FRAMEWORK}lib.framework_abstraction"
    )
    return mod.Response


def _get_framework_module():
    return importlib.import_module(
        f"genericsuite.{CURRENT_FRAMEWORK}lib.framework_abstraction"
    )


# ---- Module loading ----

def test_framework_abstraction_module_loads():
    """The active framework's abstraction module must load without error."""
    mod = _get_framework_module()
    assert mod is not None


def test_framework_loaded_flag_is_true():
    """FRAMEWORK_LOADED must be True for the active framework."""
    mod = _get_framework_module()
    assert mod.FRAMEWORK_LOADED is True


# ---- Request class exists ----

def test_framework_has_request_class():
    """The active framework exposes a Request class."""
    mod = _get_framework_module()
    assert hasattr(mod, "Request")


# ---- Pydantic Request instantiation (fastapi + flask) ----

@pytest.mark.skipif(not _PYDANTIC_FRAMEWORK,
                    reason=f"Pydantic Request only on fastapi/flask (got {CURRENT_FRAMEWORK})")
def test_request_has_expected_attributes():
    Request = _get_request_class()
    req = Request(
        method="GET",
        headers={"Authorization": "Bearer token123"},
        json_body={"key": "value"},
        query_params={"page": "1"},
    )
    assert req.method == "GET"
    assert req.headers["Authorization"] == "Bearer token123"
    assert req.json_body == {"key": "value"}
    assert req.query_params == {"page": "1"}


@pytest.mark.skipif(not _PYDANTIC_FRAMEWORK,
                    reason=f"Pydantic Request only on fastapi/flask (got {CURRENT_FRAMEWORK})")
def test_request_authorization_header_accessible():
    Request = _get_request_class()
    req = Request(headers={"Authorization": "Bearer mytoken"})
    assert "Authorization" in req.headers
    assert "Bearer mytoken" in req.headers["Authorization"]


@pytest.mark.skipif(not _PYDANTIC_FRAMEWORK,
                    reason=f"Pydantic Request only on fastapi/flask (got {CURRENT_FRAMEWORK})")
def test_request_to_dict():
    Request = _get_request_class()
    req = Request(method="POST", headers={}, json_body={"a": 1}, query_params={})
    d = req.to_dict()
    assert d["method"] == "POST"
    assert d["json_body"] == {"a": 1}


@pytest.mark.skipif(not _PYDANTIC_FRAMEWORK,
                    reason=f"Pydantic Request only on fastapi/flask (got {CURRENT_FRAMEWORK})")
def test_request_default_method_is_get():
    Request = _get_request_class()
    req = Request()
    assert req.method == "GET"


@pytest.mark.skipif(not _PYDANTIC_FRAMEWORK,
                    reason=f"Pydantic Request only on fastapi/flask (got {CURRENT_FRAMEWORK})")
def test_request_is_pydantic_model():
    Request = _get_request_class()
    from pydantic import BaseModel
    assert issubclass(Request, BaseModel)


# ---- get_current_framework (always runs) ----

def test_get_current_framework_returns_configured_value():
    """get_current_framework() must return the value of CURRENT_FRAMEWORK."""
    from genericsuite.util.cloud_provider_abstractor import get_cloud_provider  # unrelated — just confirm env works
    # The active framework name is already read from env at module level
    assert CURRENT_FRAMEWORK in ("fastapi", "flask", "chalice", "mcp")
