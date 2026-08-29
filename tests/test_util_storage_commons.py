"""
Tests for genericsuite/util/storage_commons.py.
"""
import sys
import types
from unittest.mock import MagicMock
from cryptography.fernet import Fernet

# Provide a real Fernet key for STORAGE_URL_SEED
_fernet_key = Fernet.generate_key().decode()

# Stub Config before storage_commons is imported
_cfg_mod = types.ModuleType("genericsuite.config.config")


class _StubCfg:
    STORAGE_URL_ENCRYPTION = "0"
    STORAGE_URL_SEED = _fernet_key
    APP_HOST_NAME = "localhost"


_cfg_mod.Config = _StubCfg
sys.modules.setdefault("genericsuite.config", types.ModuleType("genericsuite.config"))
sys.modules["genericsuite.config.config"] = _cfg_mod

# Remove previously cached storage_commons so it picks up the stub Config
for _mod in list(sys.modules):
    if "genericsuite.util.storage_commons" in _mod:
        del sys.modules[_mod]

from genericsuite.util.storage_commons import (
    get_storage_presigned_expiration_seconds,
    get_nodup_filename,
    storage_url_encryption_enabled,
    STORAGE_URL_SEPARATOR,
    DEFAULT_PRESIGNED_EXPIRATION_SECONDS,
)


def test_get_storage_presigned_expiration_seconds_default():
    result = get_storage_presigned_expiration_seconds()
    assert result == DEFAULT_PRESIGNED_EXPIRATION_SECONDS


def test_get_storage_presigned_expiration_seconds_custom():
    result = get_storage_presigned_expiration_seconds(120)
    assert result == 120


def test_get_nodup_filename_contains_original():
    result = get_nodup_filename("photo.jpg")
    assert "photo.jpg" in result


def test_get_nodup_filename_contains_date():
    result = get_nodup_filename("doc.pdf")
    # Should contain YYYY-MM-DD pattern
    import re
    assert re.search(r"\d{4}-\d{2}-\d{2}", result)


def test_get_nodup_filename_replaces_spaces():
    result = get_nodup_filename("my file.jpg")
    assert " " not in result


def test_storage_url_separator_constant():
    assert STORAGE_URL_SEPARATOR == "||"


def test_storage_url_encryption_disabled():
    assert storage_url_encryption_enabled() is False
