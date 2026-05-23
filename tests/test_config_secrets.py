"""
Tests for genericsuite/config/config_secrets.py — secrets loading.
"""
import os
import sys
from unittest.mock import patch, MagicMock


def _get_secrets_from_iaas():
    """Import the real function after mocking cloud deps."""
    for mod in list(sys.modules):
        if "genericsuite.config.config_secrets" in mod:
            del sys.modules[mod]
    mock_aws = MagicMock()
    mock_aws.get_cache_secret.return_value = {
        "error": False, "error_message": None,
        "resultset": {"SOME_SECRET": "value"}, "totalPages": None,
    }
    mock_aws.get_secrets_cache_filename.return_value = "/tmp/test_cache"
    sys.modules["genericsuite.util.aws_secrets"] = mock_aws
    sys.modules["genericsuite.util.gcp_secrets"] = MagicMock()
    sys.modules["genericsuite.util.azure_secrets"] = MagicMock()
    sys.modules["genericsuite.util.cloud_provider_abstractor"] = MagicMock()
    from genericsuite.config.config_secrets import get_secrets_from_iaas
    return get_secrets_from_iaas


def _make_logger():
    return MagicMock()


def _make_default_resultset():
    return {"error": False, "error_message": None,
            "resultset": {}, "totalPages": None}


def test_secrets_skipped_when_disabled():
    """When GET_SECRETS_ENABLED=0 no cloud call is made."""
    get_secrets_from_iaas = _get_secrets_from_iaas()
    with patch.dict(os.environ, {"GET_SECRETS_ENABLED": "0"}):
        result = get_secrets_from_iaas(_make_default_resultset, _make_logger())
    assert result["error"] is False
    # Cloud call should not have been attempted — mock aws not called
    assert sys.modules["genericsuite.util.aws_secrets"] \
        .get_cache_secret.call_count == 0


def test_secrets_called_when_enabled():
    """When GET_SECRETS_ENABLED=1 the AWS helper is invoked."""
    get_secrets_from_iaas = _get_secrets_from_iaas()
    mock_cp = MagicMock()
    mock_cp.get_cloud_provider.return_value = "AWS"
    sys.modules["genericsuite.util.cloud_provider_abstractor"] = mock_cp

    aws_mock = MagicMock()
    aws_mock.get_cache_secret.return_value = {
        "error": False, "error_message": None,
        "resultset": {}, "totalPages": None,
    }
    aws_mock.get_secrets_cache_filename.return_value = "/tmp/c"
    sys.modules["genericsuite.util.aws_secrets"] = aws_mock

    # Re-import to pick up new mocks
    for mod in list(sys.modules):
        if "genericsuite.config.config_secrets" in mod:
            del sys.modules[mod]
    from genericsuite.config.config_secrets import get_secrets_from_iaas

    with patch.dict(os.environ, {"GET_SECRETS_ENABLED": "1",
                                 "CLOUD_PROVIDER": "aws",
                                 "AWS_REGION": "us-east-1"}):
        result = get_secrets_from_iaas(_make_default_resultset, _make_logger())
    assert result["error"] is False
    aws_mock.get_cache_secret.assert_called_once()
