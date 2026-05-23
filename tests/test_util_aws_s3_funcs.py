"""
Tests for genericsuite/util/aws.py — pure function tests for S3 helpers.

Only tests functions that do not require a live AWS connection.
boto3 is mocked at module level so the import chain succeeds.
"""
import sys
from unittest.mock import MagicMock, patch


def _ensure_mocks():
    sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("boto3", MagicMock())
    sys.modules.setdefault("botocore", MagicMock())
    sys.modules.setdefault("botocore.config", MagicMock())
    sys.modules.setdefault("botocore.exceptions", MagicMock())


def _fresh_aws():
    _ensure_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.util.aws":
            del sys.modules[mod]
    import genericsuite.util.aws as m
    return m


# ---- s3_base_url ----

def test_s3_base_url_returns_correct_url():
    m = _fresh_aws()
    url = m.s3_base_url("my-bucket")
    assert url == "https://my-bucket.s3.amazonaws.com"


def test_s3_base_url_with_special_chars():
    m = _fresh_aws()
    url = m.s3_base_url("test.bucket-name")
    assert url == "https://test.bucket-name.s3.amazonaws.com"


# ---- get_bucket_key_from_url ----

def test_get_bucket_key_from_url_parses_correctly():
    m = _fresh_aws()
    bucket, key = m.get_bucket_key_from_url(
        "https://my-bucket.s3.amazonaws.com/path/to/file.txt"
    )
    assert key == "path/to/file.txt"


def test_get_bucket_key_from_url_single_level_key():
    m = _fresh_aws()
    bucket, key = m.get_bucket_key_from_url(
        "https://mybucket.s3.amazonaws.com/file.jpg"
    )
    assert key == "file.jpg"


def test_s3_base_url_module_level_constants():
    m = _fresh_aws()
    assert hasattr(m, "DEBUG")
    assert hasattr(m, "CLOUD_STORAGE_PRESIGNED_ACTIVE")
    assert isinstance(m.DEBUG, bool)


# ---- remove_from_s3 (mocked boto3) ----

def test_remove_from_s3_success():
    m = _fresh_aws()
    boto3_mock = sys.modules.get("boto3")
    if boto3_mock:
        boto3_mock.client.return_value.delete_object.return_value = {}
        with patch.object(m, "get_s3_client") as mock_client:
            mock_client.return_value.delete_object.return_value = {}
            result = m.remove_from_s3("my-bucket", "path/key.txt")
            assert result.get("error") is False


def test_remove_from_s3_exception_returns_error():
    m = _fresh_aws()
    with patch.object(m, "get_s3_client") as mock_client:
        mock_client.return_value.delete_object.side_effect = Exception("Connection error")
        result = m.remove_from_s3("my-bucket", "path/key.txt")
        assert result.get("error") is True
        assert "Failed to remove" in result.get("error_message", "")
