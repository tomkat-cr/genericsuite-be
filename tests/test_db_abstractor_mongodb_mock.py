"""
Tests for genericsuite/util/db_abstractor_mongodb.py — MongodbService and builder.

Uses the real db_abstractor_super module (bson + app_logger mocked) so that
MongodbService is a real class, not a MagicMock.
"""
import sys
import types as _t
from unittest.mock import MagicMock, patch

# Use setdefault so we don't overwrite the bson mock relied on by other tests
_bson = MagicMock()
_bson.json_util = MagicMock()
_bson.json_util.dumps = lambda x: str(x)
sys.modules.setdefault("bson", _bson)
sys.modules.setdefault("bson.json_util", _bson.json_util)
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

# Remove cached versions for a fresh import
for _mod in list(sys.modules):
    if _mod in ("genericsuite.util.db_abstractor_super",
                "genericsuite.util.db_abstractor_mongodb"):
        del sys.modules[_mod]

# Mock pymongo before import so get_order_direction works without a real install
_pymongo = _t.ModuleType("pymongo")
_pymongo.ASCENDING = 1
_pymongo.DESCENDING = -1
_pymongo.MongoClient = MagicMock()
sys.modules["pymongo"] = _pymongo

from genericsuite.util.db_abstractor_super import ObjectFactory, DbAbstract
from genericsuite.util.db_abstractor_mongodb import MongodbService, MongodbServiceBuilder


def _make_config():
    cfg = MagicMock()
    cfg.DB_CONFIG = {"app_db_uri": "mongodb://localhost/test", "app_db_name": "testdb"}
    cfg.DB_ENGINE = "MONGODB"
    return cfg


# ---- MongodbServiceBuilder singleton ----

def test_mongodb_service_builder_is_subclass_of_db_abstract():
    assert issubclass(MongodbServiceBuilder, DbAbstract)


def test_mongodb_service_builder_init():
    builder = MongodbServiceBuilder()
    assert builder._instance is None


def test_mongodb_service_is_subclass_of_db_abstract():
    assert issubclass(MongodbService, DbAbstract)


# ---- MongodbService.get_order_direction via patched init ----

def _make_service_no_init():
    """Create MongodbService without running __init__ (avoids live DB)."""
    svc = object.__new__(MongodbService)
    svc._app_config = _make_config()
    svc._db = None
    return svc


def test_mongodb_service_get_order_direction_asc():
    svc = _make_service_no_init()
    result = svc.get_order_direction("asc")
    assert result == 1  # pymongo.ASCENDING


def test_mongodb_service_get_order_direction_desc():
    svc = _make_service_no_init()
    result = svc.get_order_direction("desc")
    assert result == -1  # pymongo.DESCENDING


def test_mongodb_service_get_db_returns_db():
    svc = _make_service_no_init()
    fake_db = object()
    svc._db = fake_db
    assert svc.get_db() is fake_db
