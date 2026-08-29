"""
Tests for genericsuite/util/azure.py and genericsuite/util/gcp.py.

Smoke tests for URL-builder helpers and basic module importability.
Detailed function tests are in test_azure_storage.py and test_gcp_storage.py.
"""
import sys
import os
from unittest.mock import MagicMock, patch


def _make_config_mock():
    cfg = MagicMock()
    cfg.STORAGE_URL_ENCRYPTION = "0"
    cfg.STORAGE_URL_SEED = "xyz"
    cfg.APP_HOST_NAME = "localhost"
    cfg.TEMP_DIR = "/tmp"
    return cfg


def _ensure_mocks():
    """Ensure minimal sys.modules stubs are present so azure/gcp can import."""
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
    sys.modules.setdefault("azure", MagicMock())
    sys.modules.setdefault("azure.storage", MagicMock())
    sys.modules.setdefault("azure.storage.blob", MagicMock())
    sys.modules.setdefault("azure.identity", MagicMock())
    sys.modules.setdefault("google", MagicMock())
    sys.modules.setdefault("google.cloud", MagicMock())
    sys.modules.setdefault("google.cloud.storage", MagicMock())
    config_mod = MagicMock()
    config_mod.Config = _make_config_mock
    sys.modules["genericsuite.config.config"] = config_mod


def _fresh_azure():
    _ensure_mocks()
    for mod in list(sys.modules):
        if mod in (
            "genericsuite.util.azure",
            "genericsuite.util.utilities",
            "genericsuite.util.storage_commons",
            "genericsuite.util.encryption",
            "genericsuite.util.file_utilities",
        ):
            del sys.modules[mod]
    import genericsuite.util.azure as m
    return m


def _fresh_gcp():
    _ensure_mocks()
    for mod in list(sys.modules):
        if mod in (
            "genericsuite.util.gcp",
            "genericsuite.util.utilities",
            "genericsuite.util.storage_commons",
            "genericsuite.util.encryption",
            "genericsuite.util.file_utilities",
        ):
            del sys.modules[mod]
    import genericsuite.util.gcp as m
    return m


# ---- azure.py ----

def test_azure_blob_storage_base_url_with_account_env():
    m = _fresh_azure()
    with patch.dict(os.environ, {"AZURE_STORAGE_ACCOUNT_NAME": "mybucket"}):
        result = m.blob_storage_base_url("mybucket")
    assert "mybucket.blob.core.windows.net" in result
    assert "mybucket" in result


def test_azure_blob_storage_base_url_fallback():
    m = _fresh_azure()
    env = {k: v for k, v in os.environ.items()
           if k != "AZURE_STORAGE_ACCOUNT_NAME"}
    with patch.dict(os.environ, env, clear=True):
        result = m.blob_storage_base_url("other")
    assert "other" in result


def test_azure_remove_from_storage_sdk_error():
    m = _fresh_azure()
    with patch.object(m, "get_blob_service_client",
                      side_effect=Exception("SDK error")):
        result = m.remove_from_storage("bucket", "key/path.txt")
    assert result.get("error") is True


def test_azure_upload_file_to_storage_sdk_error():
    m = _fresh_azure()
    with patch.object(m, "get_blob_service_client",
                      side_effect=Exception("SDK error")), \
         patch.object(m, "storage_url_encryption_enabled", return_value=False), \
         patch.dict(os.environ, {"AZURE_STORAGE_ACCOUNT_NAME": "acct"}):
        result = m.upload_file_to_storage(
            "bucket", "/src/file.txt", "/dst/file.txt")
    assert result.get("error") is True


def test_azure_storage_retrieval_none_item_id():
    m = _fresh_azure()
    result = m.storage_retieval(None)
    assert result.get("error") is True


def test_azure_storage_retrieval_invalid_item_id():
    m = _fresh_azure()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      side_effect=Exception("bad")):
        result = m.storage_retieval("encrypted_item_id")
    assert result.get("error") is True


def test_azure_prepare_asset_url_raises_on_error():
    m = _fresh_azure()
    with patch.object(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE", True), \
         patch.object(m, "get_blob_presigned_url",
                      return_value={"error": True,
                                    "error_message": "SAS error"}):
        raised = False
        try:
            m.prepare_asset_url(
                "https://acct.blob.core.windows.net/c/image.jpg")
        except Exception:
            raised = True
        assert raised


# ---- gcp.py ----

def test_gcp_storage_base_url():
    m = _fresh_gcp()
    result = m.gcp_storage_base_url("mybucket")
    assert result == "https://storage.googleapis.com/mybucket"


def test_gcp_storage_base_url_custom_name():
    m = _fresh_gcp()
    assert m.gcp_storage_base_url("other-bucket") == \
        "https://storage.googleapis.com/other-bucket"


def test_gcp_remove_from_storage_sdk_error():
    m = _fresh_gcp()
    with patch.object(m, "get_gcs_client",
                      side_effect=Exception("SDK error")):
        result = m.remove_from_storage("bucket", "key/path.txt")
    assert result.get("error") is True


def test_gcp_upload_file_to_storage_sdk_error():
    m = _fresh_gcp()
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value\
        .upload_from_filename.side_effect = Exception("SDK error")
    with patch.object(m, "get_gcs_client", return_value=client_mock), \
         patch.object(m, "storage_url_encryption_enabled", return_value=False):
        result = m.upload_file_to_storage(
            "bucket", "/src/file.txt", "/dst/file.txt")
    assert result.get("error") is True


def test_gcp_storage_retrieval_none_item_id():
    m = _fresh_gcp()
    result = m.storage_retieval(None)
    assert result.get("error") is True


def test_gcp_storage_retrieval_invalid_item_id():
    m = _fresh_gcp()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      side_effect=Exception("bad")):
        result = m.storage_retieval("encrypted_item_id")
    assert result.get("error") is True


def test_gcp_prepare_asset_url_raises_on_error():
    m = _fresh_gcp()
    with patch.object(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE", True), \
         patch.object(m, "get_gcs_presigned_url",
                      return_value={"error": True,
                                    "error_message": "signing error"}):
        raised = False
        try:
            m.prepare_asset_url(
                "https://storage.googleapis.com/my-bucket/image.jpg")
        except Exception:
            raised = True
        assert raised
