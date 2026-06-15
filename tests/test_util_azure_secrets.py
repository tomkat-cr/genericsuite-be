"""
Tests for genericsuite/util/azure_secrets.py — mocked Azure KeyVault.
"""
import sys
import os
import json
import tempfile
from unittest.mock import MagicMock, patch


def _make_keyvault_mock(secret_value: str = '{"KEY": "val"}',
                         raise_exc: Exception = None):
    """Return sys.modules-compatible mocks for azure.keyvault.secrets."""
    kv_mock = MagicMock()
    identity_mock = MagicMock()
    client_instance = MagicMock()
    if raise_exc:
        client_instance.get_secret.side_effect = raise_exc
    else:
        secret_obj = MagicMock()
        secret_obj.value = secret_value
        client_instance.get_secret.return_value = secret_obj
    kv_mock.SecretClient.return_value = client_instance
    return kv_mock, identity_mock


def _fresh_import_azure_secrets(kv_mock=None, identity_mock=None):
    """Delete cached module and reimport with Azure SDK mocked."""
    for mod in list(sys.modules):
        if "genericsuite.util.azure_secrets" in mod:
            del sys.modules[mod]
    if kv_mock is None:
        kv_mock, identity_mock = _make_keyvault_mock()
    azure_mock = MagicMock()
    azure_keyvault_mock = MagicMock()
    azure_keyvault_mock.secrets = kv_mock
    azure_mock.keyvault = azure_keyvault_mock
    sys.modules["azure"] = azure_mock
    sys.modules["azure.keyvault"] = azure_keyvault_mock
    sys.modules["azure.keyvault.secrets"] = kv_mock
    sys.modules["azure.identity"] = identity_mock or MagicMock()
    sys.modules["genericsuite.util.app_logger"] = MagicMock()
    sys.modules["genericsuite.util.cloud_provider_abstractor"] = MagicMock()
    import genericsuite.util.azure_secrets as m
    return m, kv_mock


def _get_default_resultset():
    return {"error": False, "error_message": None,
            "resultset": {}, "totalPages": None}


def _make_logger():
    return MagicMock()


# ---------------------------------------------------------------------------
# Basic smoke tests
# ---------------------------------------------------------------------------

def test_azure_secrets_module_importable():
    m, _ = _fresh_import_azure_secrets()
    assert m is not None


def test_get_secrets_cache_filename_returns_string():
    m, _ = _fresh_import_azure_secrets()
    result = m.get_secrets_cache_filename("secrets")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# get_secrets — success path
# ---------------------------------------------------------------------------

def test_get_secrets_success():
    kv_mock, identity_mock = _make_keyvault_mock('{"MY_KEY": "my_value"}')
    m, _ = _fresh_import_azure_secrets(kv_mock, identity_mock)
    with patch.dict(os.environ,
                    {"AZURE_KEYVAULT_URL": "https://myvault.vault.azure.net"}):
        result = m.get_secrets(
            "myapp-test-secrets", "eastus",
            _get_default_resultset, _make_logger())
    assert result["error"] is False
    assert result["resultset"].get("MY_KEY") == "my_value"


# ---------------------------------------------------------------------------
# get_secrets — missing AZURE_KEYVAULT_URL
# ---------------------------------------------------------------------------

def test_get_secrets_missing_keyvault_url():
    m, _ = _fresh_import_azure_secrets()
    env = {k: v for k, v in os.environ.items() if k != "AZURE_KEYVAULT_URL"}
    with patch.dict(os.environ, env, clear=True):
        result = m.get_secrets(
            "myapp-test-secrets", "eastus",
            _get_default_resultset, _make_logger())
    assert result["error"] is True
    assert "AZ-GS-E010" in result["error_message"]


# ---------------------------------------------------------------------------
# get_secrets — Azure SDK raises an exception
# ---------------------------------------------------------------------------

def test_get_secrets_azure_error():
    kv_mock, identity_mock = _make_keyvault_mock(
        raise_exc=Exception("Azure API error"))
    m, _ = _fresh_import_azure_secrets(kv_mock, identity_mock)
    with patch.dict(os.environ,
                    {"AZURE_KEYVAULT_URL": "https://myvault.vault.azure.net"}):
        result = m.get_secrets(
            "myapp-test-secrets", "eastus",
            _get_default_resultset, _make_logger())
    assert result["error"] is True
    assert "AZ-GS-E020" in result["error_message"]


# ---------------------------------------------------------------------------
# get_secrets — invalid JSON value
# ---------------------------------------------------------------------------

def test_get_secrets_invalid_json():
    kv_mock, identity_mock = _make_keyvault_mock("not-valid-json")
    m, _ = _fresh_import_azure_secrets(kv_mock, identity_mock)
    with patch.dict(os.environ,
                    {"AZURE_KEYVAULT_URL": "https://myvault.vault.azure.net"}):
        result = m.get_secrets(
            "myapp-test-secrets", "eastus",
            _get_default_resultset, _make_logger())
    assert result["error"] is True
    assert "AZ-GS-E030" in result["error_message"]


# ---------------------------------------------------------------------------
# get_cache_secret — cache hit (skips Key Vault call)
# ---------------------------------------------------------------------------

def test_get_cache_secret_cache_hit():
    with tempfile.TemporaryDirectory() as tmpdir:
        m, kv_mock = _fresh_import_azure_secrets()
        cached_data = {"CACHED_KEY": "cached_value"}
        cache_path = os.path.join(tmpdir, "s_ec_test_app_test_azure.json")
        with open(cache_path, "w") as f:
            json.dump(cached_data, f)
        with patch.dict(os.environ, {
             "APP_NAME": "test_app",
             "APP_STAGE": "test",
             "AZURE_REGION": "eastus",
             "GET_SECRETS_CRITICAL": "1",
             "GET_SECRETS_ENVVARS": "0",
        }), patch.object(m, "TEMP_DIR", tmpdir):
            result = m.get_cache_secret(_get_default_resultset, _make_logger())
    assert result["error"] is False
    assert result["resultset"].get("CACHED_KEY") == "cached_value"
    kv_mock.SecretClient.assert_not_called()


# ---------------------------------------------------------------------------
# get_cache_secret — cache miss (fetches from Key Vault)
# ---------------------------------------------------------------------------

def test_get_cache_secret_cache_miss():
    kv_mock, identity_mock = _make_keyvault_mock('{"FRESH_KEY": "fresh_val"}')
    m, _ = _fresh_import_azure_secrets(kv_mock, identity_mock)
    with tempfile.TemporaryDirectory() as tmpdir, \
         patch.dict(os.environ, {
             "APP_NAME": "test_app",
             "APP_STAGE": "test",
             "AZURE_REGION": "eastus",
             "AZURE_KEYVAULT_URL": "https://myvault.vault.azure.net",
             "TEMP_DIR": tmpdir,
             "GET_SECRETS_CRITICAL": "1",
             "GET_SECRETS_ENVVARS": "0",
         }):
        result = m.get_cache_secret(_get_default_resultset, _make_logger())
    assert result["error"] is False
    assert result["resultset"].get("FRESH_KEY") == "fresh_val"
