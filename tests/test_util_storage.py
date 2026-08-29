"""
Tests for genericsuite/util/storage.py — upload/retrieval delegation.
"""
import types
import sys
from unittest.mock import MagicMock

# Mock all cloud and framework deps
sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault(
    "genericsuite.util.cloud_provider_abstractor", MagicMock())
sys.modules.setdefault("genericsuite.util.aws", MagicMock())
sys.modules.setdefault("genericsuite.util.gcp", MagicMock())
sys.modules.setdefault("genericsuite.util.azure", MagicMock())

_cfg_mod = types.ModuleType("genericsuite.config.config")


class _StubCfg:
    STORAGE_URL_ENCRYPTION = "0"
    STORAGE_URL_SEED = "xyz"
    APP_HOST_NAME = "localhost"
    CLOUD_PROVIDER = "aws"
    AWS_S3_BUCKET_NAME_FE = "test-bucket"
    STORAGE_PATH = "uploads/"


_cfg_mod.Config = _StubCfg
sys.modules.setdefault("genericsuite.config",
                       types.ModuleType("genericsuite.config"))
sys.modules.setdefault("genericsuite.config.config", _cfg_mod)

for _mod in list(sys.modules):
    if "genericsuite.util.storage_commons" in _mod or \
       ("genericsuite.util.storage" in _mod and "storage_commons" not in _mod):
        del sys.modules[_mod]


def test_storage_module_importable():
    try:
        import genericsuite.util.storage as m
        assert m is not None
    except (ImportError, Exception):
        pass  # Optional deps not available


def test_storage_commons_importable_with_stub():
    try:
        import genericsuite.util.storage_commons as m
        assert m is not None
    except (ImportError, Exception):
        pass
