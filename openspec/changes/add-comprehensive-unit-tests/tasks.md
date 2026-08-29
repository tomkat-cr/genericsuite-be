## 1. Infrastructure Setup

- [x] 1.1 Add `pytest-cov` and `pytest-mock` to `[tool.poetry.dev-dependencies]` in `pyproject.toml` and run `poetry install`
- [x] 1.2 Create `tests/conftest.py` with `set_env` autouse fixture (all required env vars), `mock_config`, `mock_db`, and `mock_request` fixtures
- [x] 1.3 Add `.coveragerc` with `[run] source = genericsuite` and `[report] fail_under = 80`; add omit entries for `__init__.py` and adapter glue modules
- [x] 1.4 Add `make test-cov` target to `Makefile` that runs `pytest --cov=genericsuite --cov-report=term-missing`

## 2. Config Tests

- [x] 2.1 Create `tests/test_config_config.py` — test `Config` attribute loading from env vars, stage-specific overrides, and default fallbacks
- [x] 2.2 Create `tests/test_config_secrets.py` — test that `get_secrets()` is skipped when `GET_SECRETS_ENABLED=0` and called when `=1` (mock boto3/azure/GCP clients)
- [x] 2.3 Create `tests/test_config_from_db.py` — test success and exception paths using a mocked DB abstractor

## 3. Core Utility Tests

- [x] 3.1 Extend `tests/test_verify_log_sanitization.py` (or create `tests/test_util_app_logger.py`) to cover `log_debug`, `log_info`, `log_warning`, `log_error` with sanitized output
- [x] 3.2 Create `tests/test_util_encryption.py` — test round-trip encrypt/decrypt and wrong-seed failure
- [x] 3.3 Create `tests/test_util_jwt.py` — test valid token decode, expired token error result, and tampered token error result
- [x] 3.4 Create `tests/test_util_passwords.py` — test hash/verify correctness, wrong-password failure, and no-plaintext-in-hash invariant
- [x] 3.5 Create `tests/test_util_utilities.py` — test `get_default_resultset`, `verify_required_fields`, and `email_verification`
- [x] 3.6 Create `tests/test_util_datetime_utilities.py` — test epoch round-trip and date string formatting
- [x] 3.7 Create `tests/test_util_file_utilities.py` — test read success and `FileNotFoundError` path using mocked `open`
- [x] 3.8 Create `tests/test_util_exceptions.py` — test that custom exceptions can be raised and caught as base classes

## 4. Security Tests

- [x] 4.1 Create `tests/test_util_security.py` — test `get_general_authorized_request` with valid JWT, missing token, expired token, and superadmin email
- [x] 4.2 Create `tests/test_util_app_context.py` — test safe identifier derivation from valid ObjectId and path-traversal inputs
- [x] 4.3 Create `tests/test_util_current_user_data.py` — test user-found, user-not-found, and DB-exception paths

## 5. Generic CRUD Tests

- [x] 5.1 Create `tests/test_util_generic_db_helpers.py` — test `find_by_id`, `list_all`, `create_item` (success and DB failure) with mocked DB abstractor
- [x] 5.2 Create `tests/test_util_generic_db_helpers_super.py` — test required-field validation blocking DB write and allowing write when all fields present
- [x] 5.3 Create `tests/test_util_generic_db_helpers_with_request.py` — test owner filter applied for regular user and skipped for admin user
- [x] 5.4 Create `tests/test_util_generic_endpoint_helpers.py` — test GET/POST/DELETE dispatch and unsupported-method error result

## 6. Framework Adapter Tests

- [x] 6.1 Create `tests/test_util_framework_abs_layer.py` — test FastAPI and Flask request normalization and Authorization header extraction
- [x] 6.2 Create `tests/test_fastapilib_framework_abstraction.py` — test success→200 and error→4xx response conversion (mock FastAPI `JSONResponse`)
- [x] 6.3 Create `tests/test_flasklib_framework_abstraction.py` — test success→200 and error result with `error_message` in body (mock Flask `Response`)
- [x] 6.4 Create `tests/test_chalicelib_framework_abstraction.py` — test Chalice adapter with mocked `chalice.Response`
- [x] 6.5 Create `tests/test_mcplib_framework_abstraction.py` — test MCP argument mapping to `Request` and result-dict to MCP response conversion

## 7. Model Tests

- [x] 7.1 Create `tests/test_models_users.py` — test `get_user_by_email` (found/not-found), `create_user` (password hashing, duplicate error)
- [x] 7.2 Create `tests/test_models_logs.py` — test log-entry insertion with newline sanitization and DB exception handling
- [x] 7.3 Create `tests/test_models_menu_options.py` — test full menu for admin and filtered menu for regular user
- [x] 7.4 Create `tests/test_models_billing.py` — test plan lookup success and unknown-plan error result
- [x] 7.5 Create `tests/test_constants_const_tables.py` — assert each exported constant is a non-empty dict or list with str/int values

## 8. Storage and Cloud Tests

- [x] 8.1 Create `tests/test_util_storage.py` — test upload delegation to AWS mock, URL retrieval, and upload failure error result
- [x] 8.2 Create `tests/test_util_cloud_provider_abstractor.py` — test factory returns correct provider class for `aws`, `gcp`, and unknown provider
- [x] 8.3 Create `tests/test_util_aws.py` — test S3 `get_object` success and `ClientError` error result (mock boto3)
- [x] 8.4 Create `tests/test_util_aws_secrets.py` — test `get_secret` with mocked Secrets Manager response
- [x] 8.5 Create `tests/test_util_azure_secrets.py` — test `get_secret` with mocked Azure `SecretClient` (patch via `sys.modules`)
- [x] 8.6 Create `tests/test_util_gcp_secrets.py` — test `get_secret` with mocked GCP `SecretManagerServiceClient` (patch via `sys.modules`)
- [x] 8.7 Create `tests/test_util_storage_commons.py` — test `build_storage_key`, allowed/disallowed extension validation

## 9. Validation and CI

- [x] 9.1 Run `make test` to confirm all existing tests still pass after conftest.py is introduced
- [x] 9.2 Run `make test-cov` and verify global coverage meets the ≥80% threshold
- [x] 9.3 Fix any import errors or test failures discovered during the coverage run
- [x] 9.4 Update `CLAUDE.md` or `README` if the `make test-cov` command is not yet documented
