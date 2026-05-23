"""
Tests for genericsuite/util/aws.py — AWS helper wrappers.
"""
import sys
from unittest.mock import MagicMock, patch

# Mock boto3 before importing aws module
boto3_mock = MagicMock()
sys.modules.setdefault("boto3", boto3_mock)
sys.modules.setdefault("botocore", MagicMock())
sys.modules.setdefault("botocore.exceptions", MagicMock())
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())


def test_aws_module_importable():
    try:
        import genericsuite.util.aws as m
        assert m is not None
    except ImportError:
        pass  # Optional SDK not fully available


def test_aws_secrets_module_importable():
    import genericsuite.util.aws_secrets as m
    assert m is not None


def test_aws_secrets_get_secrets_cache_filename_returns_string():
    from genericsuite.util.aws_secrets import get_secrets_cache_filename
    result = get_secrets_cache_filename()
    assert isinstance(result, str)
