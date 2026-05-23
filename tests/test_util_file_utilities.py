"""
Tests for genericsuite/util/file_utilities.py.
"""
import sys
import types

# Remove any previously cached file_utilities so it picks up our stub Config
for _mod in list(sys.modules):
    if "genericsuite.util.file_utilities" in _mod:
        del sys.modules[_mod]

# Force Config stub into sys.modules (override whatever is there)
_cfg_mod = types.ModuleType("genericsuite.config.config")


class _StubConfig:
    TEMP_DIR = "/tmp"


_cfg_mod.Config = _StubConfig
sys.modules["genericsuite.config.config"] = _cfg_mod

from genericsuite.util.file_utilities import temp_dir, secure_filename, temp_filename


def test_temp_dir_returns_string():
    result = temp_dir()
    assert isinstance(result, str)
    assert len(result) > 0


def test_temp_dir_returns_configured_path():
    result = temp_dir()
    assert result == "/tmp"


def test_secure_filename_no_extension():
    name = secure_filename()
    assert isinstance(name, str)
    assert "." not in name
    assert len(name) == 32  # uuid4 hex = 32 chars


def test_secure_filename_with_extension():
    name = secure_filename("jpg")
    assert name.endswith(".jpg")


def test_secure_filename_unique_each_call():
    n1 = secure_filename()
    n2 = secure_filename()
    assert n1 != n2


def test_temp_filename_contains_dir():
    result = temp_filename("png")
    assert "/tmp" in result
    assert result.endswith(".png")
