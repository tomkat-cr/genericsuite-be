"""
Tests for genericsuite/util/db_abstractor_super.py — ObjectFactory.
"""
import sys
from unittest.mock import MagicMock

# Use setdefault to avoid overwriting existing bson mock set by other tests
_bson = MagicMock()
_bson.json_util = MagicMock()
_bson.json_util.dumps = lambda x: str(x)
sys.modules.setdefault("bson", _bson)
sys.modules.setdefault("bson.json_util", _bson.json_util)
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

for _mod in list(sys.modules):
    if "genericsuite.util.db_abstractor_super" == _mod:
        del sys.modules[_mod]

from genericsuite.util.db_abstractor_super import ObjectFactory, PYMONGO_ASCENDING, PYMONGO_DESCENDING


# ---- ObjectFactory ----

def test_object_factory_register_and_create():
    factory = ObjectFactory()
    mock_builder = MagicMock(return_value="built_object")
    factory.register_builder("TEST_DB", mock_builder)
    result = factory.create("TEST_DB", app_config="cfg")
    mock_builder.assert_called_once_with(app_config="cfg")
    assert result == "built_object"


def test_object_factory_unknown_key_raises():
    factory = ObjectFactory()
    try:
        factory.create("UNKNOWN_DB")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "UNKNOWN_DB" in str(e)


def test_object_factory_multiple_builders():
    factory = ObjectFactory()
    b1 = MagicMock(return_value="db1")
    b2 = MagicMock(return_value="db2")
    factory.register_builder("DB1", b1)
    factory.register_builder("DB2", b2)
    assert factory.create("DB1") == "db1"
    assert factory.create("DB2") == "db2"


def test_object_factory_register_overwrites():
    factory = ObjectFactory()
    b1 = MagicMock(return_value="old")
    b2 = MagicMock(return_value="new")
    factory.register_builder("KEY", b1)
    factory.register_builder("KEY", b2)
    assert factory.create("KEY") == "new"


# ---- Constants ----

def test_pymongo_ascending_is_one():
    assert PYMONGO_ASCENDING == 1


def test_pymongo_descending_is_minus_one():
    assert PYMONGO_DESCENDING == -1
