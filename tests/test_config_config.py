"""
Tests for genericsuite/config/config.py — Config class.
"""
import os
import sys
import types
from unittest.mock import MagicMock


def _import_config_fresh():
    """Delete cached config modules and reimport with mocked secrets."""
    # Remove cached modules
    for mod in list(sys.modules):
        if mod in ("genericsuite.config.config",
                   "genericsuite.config.config_secrets"):
            del sys.modules[mod]

    # Stub config_secrets so get_secrets_from_iaas is a no-op
    secrets_stub = types.ModuleType("genericsuite.config.config_secrets")
    secrets_stub.get_secrets_from_iaas = lambda *a, **kw: {
        "error": False, "error_message": None, "resultset": {}, "totalPages": None
    }
    secrets_stub.get_secrets_cache_filename = lambda *a, **kw: "/tmp/test"
    sys.modules["genericsuite.config.config_secrets"] = secrets_stub

    from genericsuite.config.config import Config
    return Config


def _required_env():
    return {
        "APP_NAME": "test_app",
        "APP_STAGE": "test",
        "APP_HOST_NAME": "localhost",
        "APP_SECRET_KEY": "fake_secret_key",
        "APP_SUPERADMIN_EMAIL": "admin@test.com",
        "GIT_SUBMODULE_LOCAL_PATH": "fake_path",
        "CLOUD_PROVIDER": "aws",
        "AWS_REGION": "us-east-1",
        "GET_SECRETS_ENABLED": "0",
        "APP_DB_URI": "fake_db_uri",
        "APP_DB_ENGINE": "MONGODB",
        "APP_DB_NAME": "testdb",
        "CURRENT_FRAMEWORK": "fastapi",
        "STORAGE_URL_SEED": "xyz",
        "TEMP_DIR": "/tmp",
    }


def test_config_loads_app_name():
    Config = _import_config_fresh()
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict(
            os.environ, _required_env(), clear=False):
        cfg = Config()
    assert cfg.APP_NAME == "test_app"


def test_config_loads_stage():
    Config = _import_config_fresh()
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict(
            os.environ, _required_env(), clear=False):
        cfg = Config()
    assert cfg.STAGE == "test"


def test_config_loads_db_engine():
    Config = _import_config_fresh()
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict(
            os.environ, _required_env(), clear=False):
        cfg = Config()
    assert cfg.DB_ENGINE == "MONGODB"


def test_config_loads_db_config():
    Config = _import_config_fresh()
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict(
            os.environ, _required_env(), clear=False):
        cfg = Config()
    assert cfg.DB_CONFIG["app_db_name"] == "testdb"
    assert cfg.DB_CONFIG["app_db_uri"] == "fake_db_uri"


def test_config_loads_temp_dir():
    Config = _import_config_fresh()
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict(
            os.environ, _required_env(), clear=False):
        cfg = Config()
    assert cfg.TEMP_DIR == "/tmp"


def test_config_loads_secret_key():
    Config = _import_config_fresh()
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict(
            os.environ, _required_env(), clear=False):
        cfg = Config()
    assert cfg.APP_SECRET_KEY == "fake_secret_key"
