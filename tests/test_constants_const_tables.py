"""
Tests for genericsuite/constants/const_tables.py — get_constant.
"""
import sys
from unittest.mock import MagicMock, patch

# Mock get_json_def_both to return predictable constant data
_cfg_dbdef_mock = MagicMock()
_cfg_dbdef_mock.get_json_def_both.return_value = {
    "STATUS_CHOICES": {"1": "Active", "0": "Inactive"},
    "BOOL_CHOICES": {"1": "Yes", "0": "No"},
}
sys.modules.setdefault("genericsuite.util.config_dbdef_helpers", _cfg_dbdef_mock)

# Remove any previously loaded const_tables module to force re-import
for _mod in list(sys.modules):
    if "genericsuite.constants.const_tables" in _mod:
        del sys.modules[_mod]

from genericsuite.constants.const_tables import get_constant, constants


def test_constants_dict_is_not_empty():
    assert isinstance(constants, dict)
    assert len(constants) > 0


def test_get_constant_returns_all_entries_when_no_entry_name():
    result = get_constant("STATUS_CHOICES")
    assert isinstance(result, dict)
    assert "1" in result


def test_get_constant_returns_specific_entry():
    result = get_constant("STATUS_CHOICES", "1")
    assert result == "Active"


def test_get_constant_returns_default_for_missing_entry():
    result = get_constant("STATUS_CHOICES", "missing_key", "default_val")
    assert result == "default_val"


def test_constant_values_are_strings():
    """All values in STATUS_CHOICES are strings."""
    choices = get_constant("STATUS_CHOICES")
    for value in choices.values():
        assert isinstance(value, str)
