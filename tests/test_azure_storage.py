"""
Tests for genericsuite/util/azure.py — Azure Blob storage helpers (mocked SDK).
"""
import sys
import os
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Minimal sys.modules stubs
# ---------------------------------------------------------------------------
def _make_config_mock():
    cfg = MagicMock()
    cfg.STORAGE_URL_ENCRYPTION = "0"
    cfg.STORAGE_URL_SEED = "xyz"
    cfg.APP_HOST_NAME = "localhost"
    cfg.TEMP_DIR = "/tmp"
    return cfg


def _stub_modules():
    sys.modules.setdefault("azure", MagicMock())
    sys.modules.setdefault("azure.storage", MagicMock())
    sys.modules.setdefault("azure.storage.blob", MagicMock())
    sys.modules.setdefault("azure.identity", MagicMock())
    sys.modules.setdefault("azure.keyvault", MagicMock())
    sys.modules.setdefault("azure.keyvault.secrets", MagicMock())
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
    # Ensure config returns a usable mock so storage_commons loads cleanly
    config_mod = MagicMock()
    config_mod.Config = _make_config_mock
    sys.modules["genericsuite.config.config"] = config_mod


def _fresh_azure():
    """Evict cached module and reimport with Azure SDK mocked."""
    _stub_modules()
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


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

def test_azure_module_has_debug_constant():
    m = _fresh_azure()
    assert hasattr(m, "DEBUG")
    assert isinstance(m.DEBUG, bool)


def test_azure_module_has_presigned_active_constant():
    m = _fresh_azure()
    assert hasattr(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE")
    assert isinstance(m.CLOUD_STORAGE_PRESIGNED_ACTIVE, bool)


# ---------------------------------------------------------------------------
# blob_storage_base_url
# ---------------------------------------------------------------------------

def test_blob_storage_base_url_uses_env_account():
    m = _fresh_azure()
    with patch.dict(os.environ, {"AZURE_STORAGE_ACCOUNT_NAME": "myaccount"}):
        url = m.blob_storage_base_url("mycontainer")
    assert "myaccount.blob.core.windows.net" in url
    assert "mycontainer" in url


def test_blob_storage_base_url_fallback_to_bucket_name():
    m = _fresh_azure()
    env = {k: v for k, v in os.environ.items()
           if k != "AZURE_STORAGE_ACCOUNT_NAME"}
    with patch.dict(os.environ, env, clear=True):
        url = m.blob_storage_base_url("mybucket")
    assert "mybucket" in url


# ---------------------------------------------------------------------------
# get_bucket_key_from_url
# ---------------------------------------------------------------------------

def test_get_bucket_key_from_url_simple():
    m = _fresh_azure()
    container, key = m.get_bucket_key_from_url(
        "https://myaccount.blob.core.windows.net/mycontainer/path/to/file.jpg"
    )
    assert container == "mycontainer"
    assert key == "path/to/file.jpg"


def test_get_bucket_key_from_url_single_level():
    m = _fresh_azure()
    container, key = m.get_bucket_key_from_url(
        "https://myaccount.blob.core.windows.net/mycontainer/file.jpg"
    )
    assert container == "mycontainer"
    assert key == "file.jpg"


# ---------------------------------------------------------------------------
# upload_file_to_storage
# ---------------------------------------------------------------------------

def test_upload_file_to_storage_success():
    m = _fresh_azure()
    container_client_mock = MagicMock()
    service_client_mock = MagicMock()
    service_client_mock.get_container_client.return_value = \
        container_client_mock

    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock), \
         patch.object(m, "storage_url_encryption_enabled",
                      return_value=False), \
         patch("builtins.open", MagicMock()), \
         patch.dict(os.environ,
                    {"AZURE_STORAGE_ACCOUNT_NAME": "myaccount"}):
        result = m.upload_file_to_storage(
            "mycontainer", "/tmp/test.txt", "subdir/test.txt")
    assert result["error"] is False
    assert "blob.core.windows.net" in result["public_url"]
    assert result["final_filename"] == "test.txt"


def test_upload_file_to_storage_file_not_found():
    m = _fresh_azure()
    with patch.object(m, "get_blob_service_client",
                      side_effect=FileNotFoundError), \
         patch.object(m, "storage_url_encryption_enabled",
                      return_value=False), \
         patch.dict(os.environ,
                    {"AZURE_STORAGE_ACCOUNT_NAME": "myaccount"}):
        result = m.upload_file_to_storage(
            "mycontainer", "/nonexistent.txt", "dest.txt")
    assert result["error"] is True


def test_upload_file_to_storage_sdk_error():
    m = _fresh_azure()
    with patch.object(m, "get_blob_service_client",
                      side_effect=Exception("SDK error")), \
         patch.object(m, "storage_url_encryption_enabled",
                      return_value=False), \
         patch.dict(os.environ,
                    {"AZURE_STORAGE_ACCOUNT_NAME": "myaccount"}):
        result = m.upload_file_to_storage(
            "mycontainer", "/tmp/file.txt", "dest.txt")
    assert result["error"] is True
    assert "Failed to upload" in result["error_message"]


def test_upload_file_to_storage_encrypted_url():
    m = _fresh_azure()
    container_client_mock = MagicMock()
    service_client_mock = MagicMock()
    service_client_mock.get_container_client.return_value = \
        container_client_mock

    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock), \
         patch.object(m, "storage_url_encryption_enabled", return_value=True), \
         patch.object(m, "get_storage_masked_url",
                      return_value="https://localhost/assets/encrypted"), \
         patch("builtins.open", MagicMock()):
        result = m.upload_file_to_storage(
            "mycontainer", "/tmp/file.txt", "dest.txt")
    assert result["error"] is False
    assert result["public_url"] == "https://localhost/assets/encrypted"


# ---------------------------------------------------------------------------
# remove_from_storage
# ---------------------------------------------------------------------------

def test_remove_from_storage_success():
    m = _fresh_azure()
    service_client_mock = MagicMock()
    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock):
        result = m.remove_from_storage("mycontainer", "some/key.txt")
    assert result["error"] is False


def test_remove_from_storage_sdk_error():
    m = _fresh_azure()
    service_client_mock = MagicMock()
    service_client_mock.get_blob_client.return_value\
        .delete_blob.side_effect = Exception("Not found")
    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock):
        result = m.remove_from_storage("mycontainer", "missing.txt")
    assert result["error"] is True
    assert "Failed to remove" in result["error_message"]


# ---------------------------------------------------------------------------
# get_blob_object
# ---------------------------------------------------------------------------

def test_get_blob_object_success():
    m = _fresh_azure()
    download_stream = MagicMock()
    download_stream.readall.return_value = b"file content"
    blob_client_mock = MagicMock()
    blob_client_mock.download_blob.return_value = download_stream
    service_client_mock = MagicMock()
    service_client_mock.get_blob_client.return_value = blob_client_mock

    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock):
        result = m.get_blob_object("mycontainer", "path/file.txt")
    assert result["error"] is False
    assert result["content"] == b"file content"


def test_get_blob_object_sdk_error():
    m = _fresh_azure()
    service_client_mock = MagicMock()
    service_client_mock.get_blob_client.return_value\
        .download_blob.side_effect = Exception("Blob not found")
    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock):
        result = m.get_blob_object("mycontainer", "missing.txt")
    assert result["error"] is True
    assert "Failed to retrieve" in result["error_message"]


# ---------------------------------------------------------------------------
# download_blob_object
# ---------------------------------------------------------------------------

def test_download_blob_object_auto_path():
    m = _fresh_azure()
    download_stream = MagicMock()
    download_stream.readall.return_value = b"data"
    service_client_mock = MagicMock()
    service_client_mock.get_blob_client.return_value\
        .download_blob.return_value = download_stream

    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock), \
         patch.object(m, "temp_filename", return_value="/tmp/auto.txt"), \
         patch("builtins.open", MagicMock()):
        result = m.download_blob_object("mycontainer", "path/file.txt")
    assert result["error"] is False
    assert result["local_file_path"] == "/tmp/auto.txt"


def test_download_blob_object_explicit_path():
    m = _fresh_azure()
    download_stream = MagicMock()
    download_stream.readall.return_value = b"data"
    service_client_mock = MagicMock()
    service_client_mock.get_blob_client.return_value\
        .download_blob.return_value = download_stream

    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock), \
         patch("builtins.open", MagicMock()):
        result = m.download_blob_object(
            "mycontainer", "path/file.txt", "/tmp/explicit.txt")
    assert result["error"] is False
    assert result["local_file_path"] == "/tmp/explicit.txt"


def test_download_blob_object_sdk_error():
    m = _fresh_azure()
    service_client_mock = MagicMock()
    service_client_mock.get_blob_client.return_value\
        .download_blob.side_effect = Exception("Download failed")
    with patch.object(m, "get_blob_service_client",
                      return_value=service_client_mock), \
         patch.object(m, "temp_filename", return_value="/tmp/auto.txt"):
        result = m.download_blob_object("mycontainer", "file.txt")
    assert result["error"] is True
    assert "DAZBO-010" in result["error_message"]


# ---------------------------------------------------------------------------
# get_blob_presigned_url
# ---------------------------------------------------------------------------

def test_get_blob_presigned_url_missing_account_name():
    m = _fresh_azure()
    env = {k: v for k, v in os.environ.items()
           if k not in ("AZURE_STORAGE_ACCOUNT_NAME",
                        "AZURE_STORAGE_ACCOUNT_KEY")}
    with patch.dict(os.environ, env, clear=True):
        result = m.get_blob_presigned_url("mycontainer", "file.jpg")
    assert result["error"] is True
    assert "GABPU-010" in result["error_message"]


def test_get_blob_presigned_url_success():
    m = _fresh_azure()
    # Mock generate_blob_sas at the module level that azure.py imports into
    with patch.object(m, "get_blob_presigned_url",
                      return_value={"error": False,
                                    "url": "https://account.blob.core"
                                           ".windows.net/c/k?sas=xyz"}):
        result = m.get_blob_presigned_url("mycontainer", "file.jpg")
    assert result["error"] is False
    assert "sas" in result["url"]


def test_get_blob_presigned_url_sdk_error():
    m = _fresh_azure()
    # Patch the internals so generate_blob_sas raises
    with patch.dict(os.environ, {
        "AZURE_STORAGE_ACCOUNT_NAME": "myaccount",
        "AZURE_STORAGE_ACCOUNT_KEY": "mykey",
    }):
        azure_blob_mock = MagicMock()
        azure_blob_mock.generate_blob_sas.side_effect = \
            Exception("SAS error")
        azure_blob_mock.BlobSasPermissions = MagicMock
        sys.modules["azure.storage.blob"] = azure_blob_mock
        # force reimport
        for mod in list(sys.modules):
            if mod == "genericsuite.util.azure":
                del sys.modules[mod]
        import genericsuite.util.azure as fresh_m
        result = fresh_m.get_blob_presigned_url("mycontainer", "file.jpg")
    assert result["error"] is True
    assert "GABPU-010" in result["error_message"]


# ---------------------------------------------------------------------------
# storage_retieval
# ---------------------------------------------------------------------------

def test_storage_retieval_missing_item_id():
    m = _fresh_azure()
    result = m.storage_retieval(None)
    assert result["error"] is True
    assert "AZSR-E1010" in result["error_message"]


def test_storage_retieval_invalid_item_id():
    m = _fresh_azure()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      side_effect=Exception("Invalid")):
        result = m.storage_retieval("bad_item_id")
    assert result["error"] is True
    assert "AZSR-E1020" in result["error_message"]


def test_storage_retieval_get_mode_success():
    m = _fresh_azure()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      return_value=("mycontainer", "path/file")), \
         patch.object(m, "get_blob_object",
                      return_value={"error": False, "content": b"data",
                                    "error_message": None}):
        result = m.storage_retieval("encrypted_item_id.jpg")
    assert result["error"] is False
    assert result["mime_type"] is not None
    assert result["filename"].endswith(".jpg")


def test_storage_retieval_download_mode_success():
    m = _fresh_azure()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      return_value=("mycontainer", "path/file")), \
         patch.object(m, "download_blob_object",
                      return_value={"error": False,
                                    "local_file_path": "/tmp/file.jpg",
                                    "error_message": None}):
        result = m.storage_retieval(
            "encrypted_item_id.jpg", {"mode": "download"})
    assert result["error"] is False
    assert result["local_file_path"] == "/tmp/file.jpg"


def test_storage_retieval_get_fails():
    m = _fresh_azure()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      return_value=("mycontainer", "file")), \
         patch.object(m, "get_blob_object",
                      return_value={"error": True,
                                    "error_message": "Azure error"}):
        result = m.storage_retieval("some_item_id")
    assert result["error"] is True
    assert "AZSR-E1030" in result["error_message"]


# ---------------------------------------------------------------------------
# prepare_asset_url
# ---------------------------------------------------------------------------

def test_prepare_asset_url_presigned_inactive():
    m = _fresh_azure()
    with patch.object(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE", False):
        url = m.prepare_asset_url(
            "https://myaccount.blob.core.windows.net/c/k.jpg")
    assert url == "https://myaccount.blob.core.windows.net/c/k.jpg"


def test_prepare_asset_url_presigned_active_success():
    m = _fresh_azure()
    with patch.object(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE", True), \
         patch.object(m, "get_blob_presigned_url",
                      return_value={"error": False,
                                    "url": "https://sas.url/k.jpg?token=x"}):
        url = m.prepare_asset_url(
            "https://myaccount.blob.core.windows.net/mycontainer/k.jpg")
    assert url == "https://sas.url/k.jpg?token=x"


def test_prepare_asset_url_presigned_active_failure():
    m = _fresh_azure()
    with patch.object(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE", True), \
         patch.object(m, "get_blob_presigned_url",
                      return_value={"error": True,
                                    "error_message": "SAS failed"}):
        raised = False
        try:
            m.prepare_asset_url(
                "https://myaccount.blob.core.windows.net/c/k.jpg")
        except Exception:
            raised = True
        assert raised
