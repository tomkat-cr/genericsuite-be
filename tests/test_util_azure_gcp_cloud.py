"""
Tests for genericsuite/util/azure.py and genericsuite/util/gcp.py.

Both modules contain stub functions that return error_resultset("Not implemented")
plus URL-builder helpers that are pure string operations.
"""
import sys
from unittest.mock import MagicMock


def _ensure_mocks():
    """Ensure minimal sys.modules stubs are present so azure/gcp can import."""
    sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())


def _fresh_azure():
    _ensure_mocks()
    # Also evict utilities so azure.py always gets the real error_resultset.
    # test_models_users.py installs a MagicMock utilities at collection time
    # (via module-level setdefault); clearing it here forces a fresh import.
    for mod in list(sys.modules):
        if mod in ("genericsuite.util.azure", "genericsuite.util.utilities"):
            del sys.modules[mod]
    import genericsuite.util.azure as m
    return m


def _fresh_gcp():
    _ensure_mocks()
    for mod in list(sys.modules):
        if mod in ("genericsuite.util.gcp", "genericsuite.util.utilities"):
            del sys.modules[mod]
    import genericsuite.util.gcp as m
    return m


# ---- azure.py ----

def test_azure_blob_storage_base_url():
    m = _fresh_azure()
    result = m.blob_storage_base_url("mybucket")
    assert result == "https://mybucket.blob.core.windows.net"


def test_azure_blob_storage_base_url_custom_name():
    m = _fresh_azure()
    assert m.blob_storage_base_url("other") == "https://other.blob.core.windows.net"


def test_azure_remove_from_storage_returns_error():
    m = _fresh_azure()
    result = m.remove_from_storage("bucket", "key/path.txt")
    assert result.get("error") is True
    assert "Not implemented" in result.get("error_message", "")


def test_azure_upload_file_to_storage_returns_error():
    m = _fresh_azure()
    result = m.upload_file_to_storage("bucket", "/src/file.txt", "/dst/file.txt")
    assert result.get("error") is True


def test_azure_upload_file_public_flag_still_returns_error():
    m = _fresh_azure()
    result = m.upload_file_to_storage("bucket", "/src", "/dst", public_file=True)
    assert result.get("error") is True


def test_azure_storage_retrieval_returns_error():
    m = _fresh_azure()
    req = MagicMock()
    bp = MagicMock()
    result = m.storage_retieval(req, bp, "encrypted_item_id")
    assert result.get("error") is True


def test_azure_storage_retrieval_none_item_id():
    m = _fresh_azure()
    result = m.storage_retieval(MagicMock(), MagicMock(), None)
    assert result.get("error") is True


def test_azure_prepare_asset_url_raises_not_implemented():
    m = _fresh_azure()
    raised = False
    try:
        m.prepare_asset_url("https://example.com/image.jpg")
    except Exception as exc:
        raised = True
        assert "Not implemented" in str(exc)
    assert raised


# ---- gcp.py ----

def test_gcp_storage_base_url():
    m = _fresh_gcp()
    result = m.gcp_storage_base_url("mybucket")
    assert result == "https://mybucket.storage.googleapis.com"


def test_gcp_storage_base_url_custom_name():
    m = _fresh_gcp()
    assert m.gcp_storage_base_url("other-bucket") == \
        "https://other-bucket.storage.googleapis.com"


def test_gcp_remove_from_storage_returns_error():
    m = _fresh_gcp()
    result = m.remove_from_storage("bucket", "key/path.txt")
    assert result.get("error") is True
    assert "Not implemented" in result.get("error_message", "")


def test_gcp_upload_file_to_storage_returns_error():
    m = _fresh_gcp()
    result = m.upload_file_to_storage("bucket", "/src/file.txt", "/dst/file.txt")
    assert result.get("error") is True


def test_gcp_upload_file_public_flag_still_returns_error():
    m = _fresh_gcp()
    result = m.upload_file_to_storage("bucket", "/src", "/dst", public_file=True)
    assert result.get("error") is True


def test_gcp_storage_retrieval_returns_error():
    m = _fresh_gcp()
    result = m.storage_retieval(MagicMock(), MagicMock(), "encrypted_item_id")
    assert result.get("error") is True


def test_gcp_storage_retrieval_none_item_id():
    m = _fresh_gcp()
    result = m.storage_retieval(MagicMock(), MagicMock(), None)
    assert result.get("error") is True


def test_gcp_prepare_asset_url_raises_not_implemented():
    m = _fresh_gcp()
    raised = False
    try:
        m.prepare_asset_url("https://example.com/image.jpg")
    except Exception as exc:
        raised = True
        assert "Not implemented" in str(exc)
    assert raised
