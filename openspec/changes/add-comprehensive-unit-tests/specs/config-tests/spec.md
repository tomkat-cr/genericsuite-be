## ADDED Requirements

### Requirement: Config class loads environment variables
The system SHALL provide a `Config` class that reads all required environment variables and exposes them as attributes. Tests SHALL use `monkeypatch.setenv` to inject values and verify attribute assignment.

#### Scenario: Required env vars are loaded
- **WHEN** `Config` is instantiated with `APP_NAME`, `APP_STAGE`, `APP_SECRET_KEY`, and `APP_DB_ENGINE` set
- **THEN** the config object attributes match the injected values

#### Scenario: Stage-specific override is applied
- **WHEN** both `APP_DB_URI` and `DEV_APP_DB_URI` are set and `APP_STAGE=dev`
- **THEN** `Config.APP_DB_URI` equals the value of `DEV_APP_DB_URI`

#### Scenario: Missing optional env var falls back to default
- **WHEN** `EXPIRATION_MINUTES` is not set
- **THEN** `Config.EXPIRATION_MINUTES` equals the documented default value

### Requirement: Config secrets loading is skipped when disabled
The system SHALL skip cloud secret manager calls when `GET_SECRETS_ENABLED=0`. The `config_secrets.py` module's cloud SDK calls SHALL be mockable via `unittest.mock.patch`.

#### Scenario: Secrets manager is not called when disabled
- **WHEN** `GET_SECRETS_ENABLED=0` and `Config` is initialised
- **THEN** no boto3 / azure / GCP SDK calls are made

#### Scenario: Secrets manager is called when enabled
- **WHEN** `GET_SECRETS_ENABLED=1` and the cloud SDK is mocked
- **THEN** `config_secrets.get_secrets()` is called exactly once

### Requirement: Config from DB returns expected structure
The `config_from_db` module SHALL return a result dict conforming to `{'error': bool, 'error_message': str|None, 'resultset': Any}` on both success and failure.

#### Scenario: DB call succeeds
- **WHEN** the underlying DB abstractor returns a valid document
- **THEN** `resultset` contains the document and `error` is `False`

#### Scenario: DB call raises an exception
- **WHEN** the underlying DB abstractor raises a runtime exception
- **THEN** `error` is `True` and `error_message` is non-empty

### Requirement: Test infrastructure: conftest.py shared fixtures
`tests/conftest.py` SHALL provide reusable pytest fixtures that inject required environment variables and return mock objects used across all test modules.

#### Scenario: set_env autouse fixture injects env vars
- **WHEN** any test in the suite runs
- **THEN** `APP_NAME`, `APP_STAGE=test`, `APP_SECRET_KEY`, `APP_DB_ENGINE=MONGODB`, `APP_DB_URI`, and `APP_SUPERADMIN_EMAIL` are set in the process environment

#### Scenario: mock_config fixture returns a Config instance
- **WHEN** a test requests the `mock_config` fixture
- **THEN** it receives a `Config` object with `APP_STAGE == "test"`

#### Scenario: pyproject.toml includes pytest-cov and pytest-mock
- **WHEN** `poetry install` is run
- **THEN** `pytest-cov` and `pytest-mock` are available as importable packages
