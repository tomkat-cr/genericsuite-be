"""
Tests for genericsuite/util/azure_secrets.py — mocked Azure KeyVault.
"""
import sys
from unittest.mock import MagicMock


def _fresh_import_azure_secrets():
    """Delete cached module and reimport with Azure SDK mocked."""
    for mod in list(sys.modules):
        if "genericsuite.util.azure_secrets" in mod:
            del sys.modules[mod]
    sys.modules["azure"] = MagicMock()
    sys.modules["azure.keyvault"] = MagicMock()
    sys.modules["azure.keyvault.secrets"] = MagicMock()
    sys.modules["azure.identity"] = MagicMock()
    sys.modules["genericsuite.util.app_logger"] = MagicMock()
    sys.modules["genericsuite.util.cloud_provider_abstractor"] = MagicMock()
    import genericsuite.util.azure_secrets as m
    return m


def test_azure_secrets_module_importable():
    m = _fresh_import_azure_secrets()
    assert m is not None


def test_get_secrets_cache_filename_returns_string():
    m = _fresh_import_azure_secrets()
    result = m.get_secrets_cache_filename("secrets")
    assert isinstance(result, str)
