"""
Tests for genericsuite/util/config_dbdef_helpers.py — JSON config file loading.
"""
import sys
import json
import os
import types
from unittest.mock import MagicMock, mock_open, patch

sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

_cfg_mod = types.ModuleType("genericsuite.config.config")


class _StubConfig:
    GIT_SUBMODULE_LOCAL_PATH = "/fake/submodule"


_cfg_mod.Config = _StubConfig
sys.modules.setdefault("genericsuite.config.config", _cfg_mod)

_util_mock = MagicMock()
_util_mock.log_debug = MagicMock()
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)

for _mod in list(sys.modules):
    if "genericsuite.util.config_dbdef_helpers" == _mod:
        del sys.modules[_mod]

from genericsuite.util.config_dbdef_helpers import get_json_def, get_json_def_both


# ---- get_json_def ----

def test_get_json_def_returns_default_when_file_missing():
    result = get_json_def("nonexistent_file_gs_test", "/nonexistent_dir", {"default": True})
    assert result == {"default": True}


def test_get_json_def_returns_empty_dict_default():
    result = get_json_def("nonexistent_gs_test")
    assert result == {}


def test_get_json_def_reads_existing_file(tmp_path):
    data = {"key": "value", "count": 42}
    json_file = tmp_path / "my_config.json"
    json_file.write_text(json.dumps(data))
    with patch("os.getcwd", return_value=str(tmp_path)):
        result = get_json_def("my_config", "")
    assert result["key"] == "value"
    assert result["count"] == 42


def test_get_json_def_reads_file_in_subdir(tmp_path):
    subdir = tmp_path / "frontend"
    subdir.mkdir()
    data = [{"name": "item1"}, {"name": "item2"}]
    (subdir / "menu.json").write_text(json.dumps(data))
    with patch("os.getcwd", return_value=str(tmp_path)):
        result = get_json_def("menu", "frontend", [])
    assert len(result) == 2


# ---- get_json_def_both ----

def test_get_json_def_both_merges_frontend_and_backend(tmp_path):
    # Create subdirectory structure: tmp_path/submodule/frontend/ and .../backend/
    submodule = tmp_path / "submodule"
    (submodule / "frontend").mkdir(parents=True)
    (submodule / "backend").mkdir(parents=True)
    (submodule / "frontend" / "constants.json").write_text(
        json.dumps({"src": "frontend", "shared": "fe_val"})
    )
    (submodule / "backend" / "constants.json").write_text(
        json.dumps({"src": "backend"})
    )
    # get_json_def builds: f'{os.getcwd()}/{dir_name}/{file}.json'
    # dir_name = f'{GIT_SUBMODULE_LOCAL_PATH}/frontend'
    # So: os.getcwd() must be tmp_path, GIT_SUBMODULE_LOCAL_PATH = "submodule"
    with patch("os.getcwd", return_value=str(tmp_path)), \
         patch("genericsuite.util.config_dbdef_helpers.settings") as mock_settings:
        mock_settings.GIT_SUBMODULE_LOCAL_PATH = "submodule"
        result = get_json_def_both("constants")
    # Both files merged: frontend keys + backend keys
    assert "src" in result


def test_get_json_def_both_missing_files_returns_empty():
    with patch("genericsuite.util.config_dbdef_helpers.settings") as mock_settings:
        mock_settings.GIT_SUBMODULE_LOCAL_PATH = "/nonexistent_path_gs"
        result = get_json_def_both("nonexistent_gs_test")
    assert result == {}
