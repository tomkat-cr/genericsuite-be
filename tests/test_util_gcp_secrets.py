"""
Tests for genericsuite/util/gcp_secrets.py — mocked GCP Secret Manager.
"""
import sys
import os
import json
import tempfile
from unittest.mock import MagicMock, patch


def _make_secretmanager_mock(secret_value: str = '{"KEY": "val"}',
                              raise_exc: Exception = None):
    """Return a sys.modules-compatible mock for google.cloud.secretmanager."""
    sm_mock = MagicMock()
    client_instance = MagicMock()
    if raise_exc:
        client_instance.access_secret_version.side_effect = raise_exc
    else:
        response = MagicMock()
        response.payload.data = secret_value.encode('utf-8')
        client_instance.access_secret_version.return_value = response
    sm_mock.SecretManagerServiceClient.return_value = client_instance
    return sm_mock


def _fresh_import_gcp_secrets(sm_mock=None):
    """Delete cached module and reimport with GCP SDK mocked."""
    for mod in list(sys.modules):
        if "genericsuite.util.gcp_secrets" in mod:
            del sys.modules[mod]
    if sm_mock is None:
        sm_mock = _make_secretmanager_mock()
    google_mock = MagicMock()
    cloud_mock = MagicMock()
    cloud_mock.secretmanager = sm_mock
    google_mock.cloud = cloud_mock
    sys.modules["google"] = google_mock
    sys.modules["google.cloud"] = cloud_mock
    sys.modules["google.cloud.secretmanager"] = sm_mock
    sys.modules["google.api_core"] = MagicMock()
    sys.modules["google.api_core.exceptions"] = MagicMock()
    sys.modules["genericsuite.util.app_logger"] = MagicMock()
    sys.modules["genericsuite.util.cloud_provider_abstractor"] = MagicMock()
    import genericsuite.util.gcp_secrets as m
    return m, sm_mock


def _get_default_resultset():
    return {"error": False, "error_message": None,
            "resultset": {}, "totalPages": None}


def _make_logger():
    return MagicMock()


# ---------------------------------------------------------------------------
# Basic smoke tests
# ---------------------------------------------------------------------------

def test_gcp_secrets_module_importable():
    m, _ = _fresh_import_gcp_secrets()
    assert m is not None


def test_get_secrets_cache_filename_returns_string():
    m, _ = _fresh_import_gcp_secrets()
    result = m.get_secrets_cache_filename("secrets")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# get_secrets — success path
# ---------------------------------------------------------------------------

def test_get_secrets_success():
    sm_mock = _make_secretmanager_mock('{"MY_KEY": "my_value"}')
    m, _ = _fresh_import_gcp_secrets(sm_mock)
    with patch.dict(os.environ, {"GCP_PROJECT_ID": "my-project"}):
        result = m.get_secrets(
            "myapp-test-secrets", "us-central1",
            _get_default_resultset, _make_logger())
    assert result["error"] is False
    assert result["resultset"].get("MY_KEY") == "my_value"


# ---------------------------------------------------------------------------
# get_secrets — missing GCP_PROJECT_ID
# ---------------------------------------------------------------------------

def test_get_secrets_missing_project_id():
    m, _ = _fresh_import_gcp_secrets()
    env = {k: v for k, v in os.environ.items() if k != "GCP_PROJECT_ID"}
    with patch.dict(os.environ, env, clear=True):
        result = m.get_secrets(
            "myapp-test-secrets", "us-central1",
            _get_default_resultset, _make_logger())
    assert result["error"] is True
    assert "G-GS-E010" in result["error_message"]


# ---------------------------------------------------------------------------
# get_secrets — GCP SDK raises an exception
# ---------------------------------------------------------------------------

def test_get_secrets_gcp_error():
    sm_mock = _make_secretmanager_mock(raise_exc=Exception("GCP API error"))
    m, _ = _fresh_import_gcp_secrets(sm_mock)
    with patch.dict(os.environ, {"GCP_PROJECT_ID": "my-project"}):
        result = m.get_secrets(
            "myapp-test-secrets", "us-central1",
            _get_default_resultset, _make_logger())
    assert result["error"] is True
    assert "G-GS-E020" in result["error_message"]


# ---------------------------------------------------------------------------
# get_secrets — invalid JSON payload
# ---------------------------------------------------------------------------

def test_get_secrets_invalid_json():
    sm_mock = _make_secretmanager_mock("not-valid-json")
    m, _ = _fresh_import_gcp_secrets(sm_mock)
    with patch.dict(os.environ, {"GCP_PROJECT_ID": "my-project"}):
        result = m.get_secrets(
            "myapp-test-secrets", "us-central1",
            _get_default_resultset, _make_logger())
    assert result["error"] is True
    assert "G-GS-E030" in result["error_message"]


# ---------------------------------------------------------------------------
# get_cache_secret — cache hit (skips GCP call)
# ---------------------------------------------------------------------------

def test_get_cache_secret_cache_hit():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fresh import AFTER tmpdir is created so TEMP_DIR can be patched
        m, sm_mock = _fresh_import_gcp_secrets()
        cached_data = {"CACHED_KEY": "cached_value"}
        cache_path = os.path.join(tmpdir, "s_ec_test_app_test_gcp.json")
        with open(cache_path, "w") as f:
            json.dump(cached_data, f)

        with patch.dict(os.environ, {
             "APP_NAME": "test_app",
             "APP_STAGE": "test",
             "GCP_REGION": "us-central1",
             "GET_SECRETS_CRITICAL": "1",
             "GET_SECRETS_ENVVARS": "0",
        }), patch.object(m, "TEMP_DIR", tmpdir):
            result = m.get_cache_secret(_get_default_resultset, _make_logger())
    assert result["error"] is False
    assert result["resultset"].get("CACHED_KEY") == "cached_value"
    # SDK client should NOT have been called
    sm_mock.SecretManagerServiceClient.assert_not_called()


# ---------------------------------------------------------------------------
# get_cache_secret — cache miss (fetches from GCP)
# ---------------------------------------------------------------------------

def test_get_cache_secret_cache_miss():
    sm_mock = _make_secretmanager_mock('{"FRESH_KEY": "fresh_value"}')
    m, _ = _fresh_import_gcp_secrets(sm_mock)
    with tempfile.TemporaryDirectory() as tmpdir, \
         patch.dict(os.environ, {
             "APP_NAME": "test_app",
             "APP_STAGE": "test",
             "GCP_REGION": "us-central1",
             "GCP_PROJECT_ID": "my-project",
             "TEMP_DIR": tmpdir,
             "GET_SECRETS_CRITICAL": "1",
             "GET_SECRETS_ENVVARS": "0",
         }):
        result = m.get_cache_secret(_get_default_resultset, _make_logger())
    assert result["error"] is False
    assert result["resultset"].get("FRESH_KEY") == "fresh_value"
