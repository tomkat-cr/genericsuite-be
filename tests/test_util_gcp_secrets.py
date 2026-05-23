"""
Tests for genericsuite/util/gcp_secrets.py — mocked GCP Secret Manager.
"""
import sys
from unittest.mock import MagicMock


def _fresh_import_gcp_secrets():
    """Delete cached module and reimport with GCP SDK mocked."""
    for mod in list(sys.modules):
        if "genericsuite.util.gcp_secrets" in mod:
            del sys.modules[mod]
    sys.modules["google"] = MagicMock()
    sys.modules["google.cloud"] = MagicMock()
    sys.modules["google.cloud.secretmanager"] = MagicMock()
    sys.modules["google.api_core"] = MagicMock()
    sys.modules["google.api_core.exceptions"] = MagicMock()
    sys.modules["genericsuite.util.app_logger"] = MagicMock()
    sys.modules["genericsuite.util.cloud_provider_abstractor"] = MagicMock()
    import genericsuite.util.gcp_secrets as m
    return m


def test_gcp_secrets_module_importable():
    m = _fresh_import_gcp_secrets()
    assert m is not None


def test_get_secrets_cache_filename_returns_string():
    m = _fresh_import_gcp_secrets()
    result = m.get_secrets_cache_filename("secrets")
    assert isinstance(result, str)
