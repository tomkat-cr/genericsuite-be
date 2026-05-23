"""
Tests for genericsuite/fastapilib/framework_abstraction.py.

These tests only run when CURRENT_FRAMEWORK=fastapi.
"""
import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower() != "fastapi",
    reason="FastAPI adapter tests only run with CURRENT_FRAMEWORK=fastapi",
)


def test_fastapi_framework_abstraction_importable():
    from genericsuite.fastapilib.framework_abstraction import Request, Response
    assert Request is not None
    assert Response is not None


def test_fastapi_framework_loaded_flag():
    from genericsuite.fastapilib import framework_abstraction
    assert framework_abstraction.FRAMEWORK_LOADED is True


def test_fastapi_request_is_pydantic_model():
    from genericsuite.fastapilib.framework_abstraction import Request
    from pydantic import BaseModel
    assert issubclass(Request, BaseModel)


def test_fastapi_request_fields_have_defaults():
    from genericsuite.fastapilib.framework_abstraction import Request
    req = Request()
    assert req.method == "GET"
    assert req.headers == {}
    assert req.json_body == {}
    assert req.query_params == {}


def test_fastapi_response_has_status_code():
    from genericsuite.fastapilib.framework_abstraction import Response
    import json
    body = json.dumps({"result": "ok"})
    resp = Response(body=body, status_code=200)
    assert resp.status_code == 200
