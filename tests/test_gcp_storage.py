"""
Tests for genericsuite/util/gcp.py — GCS storage helpers (mocked SDK).
"""
import sys
import os
from unittest.mock import MagicMock, patch, mock_open


# ---------------------------------------------------------------------------
# Minimal sys.modules stubs so gcp.py can be imported without the real SDK
# ---------------------------------------------------------------------------
def _make_config_mock():
    cfg = MagicMock()
    cfg.STORAGE_URL_ENCRYPTION = "0"
    cfg.STORAGE_URL_SEED = "xyz"
    cfg.APP_HOST_NAME = "localhost"
    cfg.TEMP_DIR = "/tmp"
    return cfg


def _stub_modules():
    gcs_mock = MagicMock()
    sys.modules.setdefault("google", MagicMock())
    sys.modules.setdefault("google.cloud", MagicMock())
    sys.modules.setdefault("google.cloud.storage", gcs_mock)
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
    # Ensure config returns a usable mock so storage_commons loads cleanly
    config_mod = MagicMock()
    config_mod.Config = _make_config_mock
    sys.modules["genericsuite.config.config"] = config_mod
    return gcs_mock


def _fresh_gcp():
    """Evict cached module and reimport with GCS SDK mocked."""
    _stub_modules()
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


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

def test_gcp_module_has_debug_constant():
    m = _fresh_gcp()
    assert hasattr(m, "DEBUG")
    assert isinstance(m.DEBUG, bool)


def test_gcp_module_has_presigned_active_constant():
    m = _fresh_gcp()
    assert hasattr(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE")
    assert isinstance(m.CLOUD_STORAGE_PRESIGNED_ACTIVE, bool)


# ---------------------------------------------------------------------------
# gcp_storage_base_url
# ---------------------------------------------------------------------------

def test_gcp_storage_base_url_format():
    m = _fresh_gcp()
    assert m.gcp_storage_base_url("my-bucket") == \
        "https://storage.googleapis.com/my-bucket"


def test_gcp_storage_base_url_other_bucket():
    m = _fresh_gcp()
    assert m.gcp_storage_base_url("other") == \
        "https://storage.googleapis.com/other"


# ---------------------------------------------------------------------------
# get_bucket_key_from_url
# ---------------------------------------------------------------------------

def test_get_bucket_key_from_url_simple():
    m = _fresh_gcp()
    bucket, key = m.get_bucket_key_from_url(
        "https://storage.googleapis.com/my-bucket/path/to/file.jpg"
    )
    assert bucket == "my-bucket"
    assert key == "path/to/file.jpg"


def test_get_bucket_key_from_url_single_level():
    m = _fresh_gcp()
    bucket, key = m.get_bucket_key_from_url(
        "https://storage.googleapis.com/my-bucket/file.jpg"
    )
    assert bucket == "my-bucket"
    assert key == "file.jpg"


# ---------------------------------------------------------------------------
# upload_file_to_storage
# ---------------------------------------------------------------------------

def test_upload_file_to_storage_success():
    m = _fresh_gcp()
    blob_mock = MagicMock()
    bucket_mock = MagicMock()
    bucket_mock.blob.return_value = blob_mock
    client_mock = MagicMock()
    client_mock.bucket.return_value = bucket_mock

    with patch.object(m, "get_gcs_client", return_value=client_mock), \
         patch.object(m, "storage_url_encryption_enabled", return_value=False):
        result = m.upload_file_to_storage(
            "my-bucket", "/tmp/test.txt", "subdir/test.txt")
    assert result["error"] is False
    assert "storage.googleapis.com" in result["public_url"]
    assert result["final_filename"] == "test.txt"


def test_upload_file_to_storage_file_not_found():
    m = _fresh_gcp()
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value\
        .upload_from_filename.side_effect = FileNotFoundError

    with patch.object(m, "get_gcs_client", return_value=client_mock), \
         patch.object(m, "storage_url_encryption_enabled", return_value=False):
        result = m.upload_file_to_storage(
            "my-bucket", "/nonexistent.txt", "dest.txt")
    assert result["error"] is True
    assert "not found" in result["error_message"]


def test_upload_file_to_storage_sdk_error():
    m = _fresh_gcp()
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value\
        .upload_from_filename.side_effect = Exception("SDK error")

    with patch.object(m, "get_gcs_client", return_value=client_mock), \
         patch.object(m, "storage_url_encryption_enabled", return_value=False):
        result = m.upload_file_to_storage(
            "my-bucket", "/tmp/file.txt", "dest.txt")
    assert result["error"] is True
    assert "Failed to upload" in result["error_message"]


def test_upload_file_to_storage_encrypted_url():
    m = _fresh_gcp()
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value\
        .upload_from_filename.return_value = None

    with patch.object(m, "get_gcs_client", return_value=client_mock), \
         patch.object(m, "storage_url_encryption_enabled", return_value=True), \
         patch.object(m, "get_storage_masked_url",
                      return_value="https://localhost/assets/encrypted"):
        result = m.upload_file_to_storage(
            "my-bucket", "/tmp/file.txt", "dest.txt")
    assert result["error"] is False
    assert result["public_url"] == "https://localhost/assets/encrypted"


# ---------------------------------------------------------------------------
# remove_from_storage
# ---------------------------------------------------------------------------

def test_remove_from_storage_success():
    m = _fresh_gcp()
    client_mock = MagicMock()
    with patch.object(m, "get_gcs_client", return_value=client_mock):
        result = m.remove_from_storage("my-bucket", "some/key.txt")
    assert result["error"] is False


def test_remove_from_storage_sdk_error():
    m = _fresh_gcp()
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value\
        .delete.side_effect = Exception("Not found")
    with patch.object(m, "get_gcs_client", return_value=client_mock):
        result = m.remove_from_storage("my-bucket", "missing.txt")
    assert result["error"] is True
    assert "Failed to remove" in result["error_message"]


# ---------------------------------------------------------------------------
# get_gcs_object
# ---------------------------------------------------------------------------

def test_get_gcs_object_success():
    m = _fresh_gcp()
    blob_mock = MagicMock()
    blob_mock.download_as_bytes.return_value = b"file content"
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value = blob_mock

    with patch.object(m, "get_gcs_client", return_value=client_mock):
        result = m.get_gcs_object("my-bucket", "path/file.txt")
    assert result["error"] is False
    assert result["content"] == b"file content"


def test_get_gcs_object_sdk_error():
    m = _fresh_gcp()
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value\
        .download_as_bytes.side_effect = Exception("Blob not found")
    with patch.object(m, "get_gcs_client", return_value=client_mock):
        result = m.get_gcs_object("my-bucket", "missing.txt")
    assert result["error"] is True
    assert "Failed to retrieve" in result["error_message"]


# ---------------------------------------------------------------------------
# download_gcs_object
# ---------------------------------------------------------------------------

def test_download_gcs_object_auto_path():
    m = _fresh_gcp()
    client_mock = MagicMock()
    with patch.object(m, "get_gcs_client", return_value=client_mock), \
         patch.object(m, "temp_filename", return_value="/tmp/auto.txt"):
        result = m.download_gcs_object("my-bucket", "path/file.txt")
    assert result["error"] is False
    assert result["local_file_path"] == "/tmp/auto.txt"


def test_download_gcs_object_explicit_path():
    m = _fresh_gcp()
    client_mock = MagicMock()
    with patch.object(m, "get_gcs_client", return_value=client_mock):
        result = m.download_gcs_object(
            "my-bucket", "path/file.txt", "/tmp/explicit.txt")
    assert result["error"] is False
    assert result["local_file_path"] == "/tmp/explicit.txt"


def test_download_gcs_object_sdk_error():
    m = _fresh_gcp()
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value\
        .download_to_filename.side_effect = Exception("Download failed")
    with patch.object(m, "get_gcs_client", return_value=client_mock), \
         patch.object(m, "temp_filename", return_value="/tmp/auto.txt"):
        result = m.download_gcs_object("my-bucket", "file.txt")
    assert result["error"] is True
    assert "DGCSO-010" in result["error_message"]


# ---------------------------------------------------------------------------
# get_gcs_presigned_url
# ---------------------------------------------------------------------------

def test_get_gcs_presigned_url_success():
    m = _fresh_gcp()
    blob_mock = MagicMock()
    blob_mock.generate_signed_url.return_value = \
        "https://signed.url/object?X-Goog-Signature=abc"
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value = blob_mock

    with patch.object(m, "get_gcs_client", return_value=client_mock):
        result = m.get_gcs_presigned_url("my-bucket", "path/file.jpg")
    assert result["error"] is False
    assert "signed.url" in result["url"]


def test_get_gcs_presigned_url_sdk_error():
    m = _fresh_gcp()
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value\
        .generate_signed_url.side_effect = Exception("No credentials")
    with patch.object(m, "get_gcs_client", return_value=client_mock):
        result = m.get_gcs_presigned_url("my-bucket", "file.jpg")
    assert result["error"] is True
    assert "GGPSU-010" in result["error_message"]


def test_get_gcs_presigned_url_custom_expiry():
    m = _fresh_gcp()
    blob_mock = MagicMock()
    blob_mock.generate_signed_url.return_value = "https://signed.url/x"
    client_mock = MagicMock()
    client_mock.bucket.return_value.blob.return_value = blob_mock

    with patch.object(m, "get_gcs_client", return_value=client_mock):
        result = m.get_gcs_presigned_url("my-bucket", "file.jpg", 120)
    assert result["error"] is False


# ---------------------------------------------------------------------------
# storage_retieval
# ---------------------------------------------------------------------------

def test_storage_retieval_missing_item_id():
    m = _fresh_gcp()
    result = m.storage_retieval(None)
    assert result["error"] is True
    assert "GSR-E1010" in result["error_message"]


def test_storage_retieval_invalid_item_id():
    m = _fresh_gcp()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      side_effect=Exception("Invalid")):
        result = m.storage_retieval("bad_item_id")
    assert result["error"] is True
    assert "GSR-E1020" in result["error_message"]


def test_storage_retieval_get_mode_success():
    m = _fresh_gcp()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      return_value=("my-bucket", "path/file")), \
         patch.object(m, "get_gcs_object",
                      return_value={"error": False, "content": b"data",
                                    "error_message": None}):
        result = m.storage_retieval("encrypted_item_id.jpg")
    assert result["error"] is False
    assert result["mime_type"] is not None
    assert result["filename"].endswith(".jpg")


def test_storage_retieval_download_mode_success():
    m = _fresh_gcp()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      return_value=("my-bucket", "path/file")), \
         patch.object(m, "download_gcs_object",
                      return_value={"error": False,
                                    "local_file_path": "/tmp/file.jpg",
                                    "error_message": None}):
        result = m.storage_retieval(
            "encrypted_item_id.jpg", {"mode": "download"})
    assert result["error"] is False
    assert result["local_file_path"] == "/tmp/file.jpg"


def test_storage_retieval_get_fails():
    m = _fresh_gcp()
    with patch.object(m, "get_bucket_key_from_decripted_item_id",
                      return_value=("my-bucket", "file")), \
         patch.object(m, "get_gcs_object",
                      return_value={"error": True,
                                    "error_message": "GCS error"}):
        result = m.storage_retieval("some_item_id")
    assert result["error"] is True
    assert "GSR-E1030" in result["error_message"]


# ---------------------------------------------------------------------------
# prepare_asset_url
# ---------------------------------------------------------------------------

def test_prepare_asset_url_presigned_inactive():
    m = _fresh_gcp()
    with patch.object(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE", False):
        url = m.prepare_asset_url("https://storage.googleapis.com/b/k.jpg")
    assert url == "https://storage.googleapis.com/b/k.jpg"


def test_prepare_asset_url_presigned_active_success():
    m = _fresh_gcp()
    with patch.object(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE", True), \
         patch.object(m, "get_gcs_presigned_url",
                      return_value={"error": False,
                                    "url": "https://signed.url/k.jpg"}):
        url = m.prepare_asset_url(
            "https://storage.googleapis.com/my-bucket/k.jpg")
    assert url == "https://signed.url/k.jpg"


def test_prepare_asset_url_presigned_active_failure():
    m = _fresh_gcp()
    with patch.object(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE", True), \
         patch.object(m, "get_gcs_presigned_url",
                      return_value={"error": True,
                                    "error_message": "signing failed"}):
        raised = False
        try:
            m.prepare_asset_url(
                "https://storage.googleapis.com/my-bucket/k.jpg")
        except Exception:
            raised = True
        assert raised
