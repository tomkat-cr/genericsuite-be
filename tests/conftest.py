"""
Shared pytest fixtures for genericsuite-be tests.

Sets required environment variables at module level so they are in place
before any test module imports project code.
"""
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Required env vars — set before any project module is imported
# ---------------------------------------------------------------------------
_ENV_DEFAULTS = {
    "APP_NAME": "test_app",
    "APP_STAGE": "test",
    "APP_HOST_NAME": "localhost",
    "APP_SECRET_KEY": "fake_secret_key_for_tests_only",
    "APP_SUPERADMIN_EMAIL": "superadmin@test.com",
    "GIT_SUBMODULE_LOCAL_PATH": "fake_path",
    "CLOUD_PROVIDER": "aws",
    "AWS_REGION": "us-east-1",
    "GET_SECRETS_ENABLED": "0",
    "APP_DB_URI": "fake_db_uri",
    "APP_DB_ENGINE": "MONGODB",
    "APP_DB_NAME": "mongo",
    "CURRENT_FRAMEWORK": "fastapi",
    "STORAGE_URL_SEED": "xyz",
    "TEMP_DIR": "/tmp",
}

for _k, _v in _ENV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def env_vars(monkeypatch):
    """Ensure all required env vars are set for the duration of a test."""
    for key, value in _ENV_DEFAULTS.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_db():
    """Return a MagicMock that acts as a DB abstractor."""
    db = MagicMock()
    db.find_one.return_value = None
    db.find.return_value = []
    db.insert_one.return_value = MagicMock(inserted_id="fake_id")
    db.update_one.return_value = MagicMock(modified_count=1)
    db.delete_one.return_value = MagicMock(deleted_count=1)
    db.count_documents.return_value = 0
    return db


@pytest.fixture
def mock_request():
    """Return a minimal framework-agnostic mock Request."""
    req = MagicMock()
    req.method = "GET"
    req.headers = {}
    req.json_body = {}
    req.query_params = {}
    return req


@pytest.fixture
def mock_config():
    """Return a minimal mock Config object with test values."""
    cfg = MagicMock()
    cfg.APP_NAME = "test_app"
    cfg.APP_STAGE = "test"
    cfg.APP_SECRET_KEY = "fake_secret_key_for_tests_only"
    cfg.APP_HOST_NAME = "localhost"
    cfg.APP_DB_ENGINE = "MONGODB"
    cfg.APP_DB_NAME = "mongo"
    cfg.APP_SUPERADMIN_EMAIL = "superadmin@test.com"
    cfg.HEADER_TOKEN_ENTRY_NAME = "x-access-token"
    cfg.STORAGE_URL_ENCRYPTION = "0"
    cfg.STORAGE_URL_SEED = "xyz"
    cfg.TEMP_DIR = "/tmp"
    cfg.DEBUG = False
    return cfg
