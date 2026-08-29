"""
Tests for genericsuite/util/cloud_provider_abstractor.py.
"""
import os
from unittest.mock import patch

from genericsuite.util.cloud_provider_abstractor import (
    get_cloud_provider,
    get_cloud_region,
)


def test_get_cloud_provider_aws():
    with patch.dict(os.environ, {"CLOUD_PROVIDER": "aws"}):
        result = get_cloud_provider()
    assert result == "AWS"


def test_get_cloud_provider_gcp():
    with patch.dict(os.environ, {"CLOUD_PROVIDER": "gcp"}):
        result = get_cloud_provider()
    assert result == "GCP"


def test_get_cloud_provider_azure():
    with patch.dict(os.environ, {"CLOUD_PROVIDER": "azure"}):
        result = get_cloud_provider()
    assert result == "AZURE"


def test_get_cloud_provider_case_insensitive():
    with patch.dict(os.environ, {"CLOUD_PROVIDER": "Aws"}):
        result = get_cloud_provider()
    assert result == "AWS"


def test_get_cloud_provider_missing_raises():
    with patch.dict(os.environ, {}, clear=True):
        try:
            get_cloud_provider()
            assert False, "Should have raised"
        except Exception as e:
            assert "CLOUD_PROVIDER" in str(e)


def test_get_cloud_provider_unsupported_raises():
    with patch.dict(os.environ, {"CLOUD_PROVIDER": "unknown"}):
        try:
            get_cloud_provider()
            assert False, "Should have raised"
        except Exception as e:
            assert "not supported" in str(e).lower() or "CLOUD_PROVIDER" in str(e)


def test_get_cloud_region_aws():
    with patch.dict(os.environ, {"CLOUD_PROVIDER": "aws", "AWS_REGION": "us-west-2"}):
        result = get_cloud_region()
    assert result == "us-west-2"


def test_get_cloud_region_gcp():
    with patch.dict(os.environ, {"CLOUD_PROVIDER": "gcp", "GCP_REGION": "us-central1"}):
        result = get_cloud_region()
    assert result == "us-central1"
