## Why

The project has ~80 source modules but only 6 test files, all focused on DB abstractor operator translation — leaving config, utilities, security, JWT, passwords, CRUD helpers, framework adapters, models, and cloud integrations entirely untested. Expanding pytest coverage to all functions and classes will catch regressions early, enforce the documented error-return contract, and provide a safety net for future refactoring.

## What Changes

- Add pytest test files covering every public function and class in `genericsuite/`
- Use `unittest.mock` / `pytest-mock` to isolate external dependencies (databases, cloud providers, SMTP, filesystem)
- Establish a `conftest.py` with shared fixtures (env vars, mock DB, mock Config)
- Add `pytest-cov` reporting to surface coverage metrics in CI (`make test`)
- Extend `Makefile` with a `make test-cov` target that enforces a minimum coverage threshold

Modules covered (currently zero test coverage):
- `config/config.py`, `config/config_secrets.py`, `config/config_from_db.py`
- `util/app_logger.py` (extend existing), `util/encryption.py`, `util/jwt.py`, `util/passwords.py`
- `util/utilities.py`, `util/datetime_utilities.py`, `util/file_utilities.py`
- `util/security.py`, `util/app_context.py`, `util/current_user_data.py`
- `util/generic_db_helpers.py`, `util/generic_db_helpers_super.py`, `util/generic_endpoint_helpers.py`
- `util/framework_abs_layer.py`, `util/nav_helpers.py`, `util/schema_utilities.py`
- `util/cloud_provider_abstractor.py`, `util/storage.py`, `util/storage_commons.py`
- `util/exceptions.py`, `util/request_handler.py`, `util/parse_multipart.py`
- `models/users/users.py`, `models/logs/logs.py`, `models/menu_options/menu_options.py`, `models/billing/billing_utilities.py`
- `constants/const_tables.py`
- `fastapilib/`, `flasklib/`, `chalicelib/`, `mcplib/` framework adapters and endpoints

## Capabilities

### New Capabilities

- `config-tests`: Unit tests for the Config class, environment-variable loading, stage-specific overrides, and cloud secret manager integration (mocked)
- `core-util-tests`: Unit tests for app_logger, encryption, jwt, passwords, utilities, datetime_utilities, file_utilities, exceptions, and request_handler
- `security-tests`: Unit tests for security.py (authorization checks, JWT validation, group-based access), app_context.py, and current_user_data.py
- `generic-crud-tests`: Unit tests for GenericDbHelper, GenericDbHelperSuper, GenericDbHelperWithRequest, and GenericEndpointHelper using mock DB backends
- `framework-adapter-tests`: Unit tests for framework_abstraction.py and framework_abs_layer.py across FastAPI, Flask, Chalice, and MCP adapters
- `model-tests`: Unit tests for users, logs, menu_options, and billing model helpers
- `storage-cloud-tests`: Unit tests for storage.py, storage_commons.py, cloud_provider_abstractor.py, and the aws/azure/gcp helpers (all cloud calls mocked)

### Modified Capabilities

## Impact

- `tests/` directory: new test files and `conftest.py`
- `Makefile`: new `test-cov` target; existing `make test` unchanged
- `pyproject.toml`: add `pytest-cov` and `pytest-mock` as dev dependencies
- No production code changes; all new code is test-only
