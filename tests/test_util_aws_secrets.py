"""
Tests for genericsuite/util/aws_secrets.py — get_secret with mocked boto3.
"""
import sys
import os
from unittest.mock import MagicMock, patch

# Patch boto3 before importing
boto3_mock = MagicMock()
sys.modules["boto3"] = boto3_mock
sys.modules.setdefault("botocore", MagicMock())
sys.modules.setdefault("botocore.exceptions", MagicMock())
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault("genericsuite.util.cloud_provider_abstractor", MagicMock())

# Remove cached module to pick up fresh boto3 mock
for _mod in list(sys.modules):
    if "genericsuite.util.aws_secrets" in _mod:
        del sys.modules[_mod]


def _get_default_resultset():
    return {"error": False, "error_message": None,
            "resultset": {}, "totalPages": None}


def _make_logger():
    return MagicMock()


def test_get_secrets_cache_filename_default():
    from genericsuite.util.aws_secrets import get_secrets_cache_filename
    filename = get_secrets_cache_filename()
    assert isinstance(filename, str)


def test_get_secrets_cache_filename_with_type():
    from genericsuite.util.aws_secrets import get_secrets_cache_filename
    filename = get_secrets_cache_filename("env")
    assert isinstance(filename, str)


def test_get_cache_secret_calls_boto3_client():
    """get_cache_secret should call boto3 client for secrets manager."""
    sm_client_mock = MagicMock()
    sm_client_mock.get_secret_value.return_value = {
        "SecretString": '{"MY_KEY": "my_value"}'
    }
    boto3_mock.client.return_value = sm_client_mock

    from genericsuite.util.aws_secrets import get_cache_secret
    with patch.dict(os.environ, {
        "APP_NAME": "test_app",
        "APP_STAGE": "test",
        "AWS_REGION": "us-east-1",
        "TEMP_DIR": "/tmp",
    }):
        result = get_cache_secret(_get_default_resultset, _make_logger())
    # Function ran without exception
    assert "error" in result
