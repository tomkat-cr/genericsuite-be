# CLAUDE.md

This file provides guidance to AI Coding Assistants (Claude Code, Gemini CLI, Cursor, Antigravity, etc.) when working with code in this repository.

## Project overview

GenericSuite Core is a **framework-agnostic backend library** for Python APIs. It lets projects swap frameworks (FastAPI, Flask, Chalice, MCP) and databases (MongoDB, DynamoDB, PostgreSQL, MySQL, Supabase) with minimal code changes. All configuration is driven by environment variables and JSON config files.

It is part of a larger ecosystem of GenericSuite projects, including a web frontend (genericsuite-fe) and mobile packages (genericsuite-mobile). For more information about the GenericSuite ecosystem, see the [GenericSuite Basecamp](https://github.com/tomkat-cr/genericsuite-basecamp).

## Architecture

### Framework Abstraction

Each supported framework lives in its own `*lib/` package (`fastapilib/`, `flasklib/`, `chalicelib/`, `mcplib/`), with parallel structure:
- `framework_abstraction.py` — normalizes incoming requests into a common `Request` object and outgoing responses
- `endpoints/` — framework-specific endpoint wiring (users, logs, menu_options, storage)
- `util/` — framework-specific helpers (e.g., Chalice CORS, FastAPI middleware)

### Database Abstraction

`genericsuite/util/db_abstractor.py` is the main factory. It reads `APP_DB_ENGINE` at runtime and returns the appropriate backend via `ObjectFactory`:

```
db_abstractor_super.py          ← base classes / factory registration
db_abstractor_mongodb.py        ← pymongo
db_abstractor_dynamodb.py       ← boto3
db_abstractor_sql.py            ← SQLAlchemy base
db_abstractor_postgresql.py     ← PostgreSQL (extends SQL)
db_abstractor_mysql.py          ← MySQL (extends SQL)
db_abstractor_supabase.py       ← Supabase/PostgreSQL
db_abstractor_elem_match.py     ← $elemMatch operator support
```

All backends implement the same interface (`find`, `update_one`, `delete_one`, `count`, etc.) and translate MongoDB-style query operators (`$regex`, `$in`, `$gt`, `$push`, `$pull`, `$elemMatch`, …) to the native query language.

### Generic CRUD Layer

`generic_db_helpers.py` / `generic_db_helpers_super.py` provide `GenericDbHelper`, the base class for table-level operations driven by JSON config files. `generic_endpoint_helpers.py` provides `GenericEndpointHelper`, which maps HTTP verbs to CRUD operations and delegates to `GenericDbHelper`. New CRUD endpoints are created by subclassing these helpers rather than writing per-endpoint code.

### Cloud Provider Abstraction

`aws.py`, `azure.py`, `gcp.py` provide cloud operations. `storage.py` is the unified storage interface; `cloud_provider_abstractor.py` is the factory. Secrets are loaded by `config/config_secrets.py` (AWS Secrets Manager, Azure KeyVault, GCP Secret Manager) when `GET_SECRETS_ENABLED=1`.

### Configuration

`config/config.py` holds the central `Config` class. It reads from environment variables; stages are `dev`, `qa`, `staging`, `prod`, `demo`. `.env.example` documents every available variable. When `APP_STAGE` matches a stage prefix for a variable, that value takes precedence.

### Request/Response Flow

```
HTTP Request
  → Framework layer (FastAPI/Flask/Chalice)
  → framework_abstraction.py  (normalize to common Request)
  → GenericEndpointHelper     (dispatch CRUD)
  → GenericDbHelper           (build filters / projection)
  → DbAbstractor              (database-specific execution)
  → Database
  → (reverse) Framework Response → Client
```

## Build and test commands

```bash
# Install dependencies
make install          # poetry install

# Run all tests (default: CURRENT_FRAMEWORK=fastapi)
make test

# Run all tests with coverage report
make test-cov

# Run tests for a specific framework
CURRENT_FRAMEWORK=fastapi make test
CURRENT_FRAMEWORK=flask   make test
CURRENT_FRAMEWORK=chalice make test
CURRENT_FRAMEWORK=mcp     make test

# Run a single test file
APP_DB_URI=fake_db_uri APP_DB_ENGINE=MONGODB APP_DB_NAME=mongo APP_NAME=test_app APP_STAGE=test APP_HOST_NAME=localhost APP_SECRET_KEY=fake_secret_key STORAGE_URL_SEED=xyz APP_SUPERADMIN_EMAIL=fake_email GIT_SUBMODULE_LOCAL_PATH=fake_path CLOUD_PROVIDER=aws AWS_REGION=us-east-1 GET_SECRETS_ENABLED=0 CURRENT_FRAMEWORK=fastapi poetry run pytest tests/test_db_abstractor_dynamodb_operators.py

# Run a single test function
... poetry run pytest tests/test_file.py::test_function_name

# Lint / type-check
poetry run mypy
poetry run pylint
poetry run flake8

# Build for PyPI
make build

# Update requirements.txt from poetry
make requirements

# Publish to PyPI
make publish

# Publish to Test PyPI
make publish-test

# SAST testing
make sast-test
```

## Testing instructions

### Testing

Tests are in `tests/` and are purely unit tests — no live database required. Each test file exercises a specific module using in-memory mocks or `sys.modules` patching. The `make test` command injects all required environment variables so no `.env` file is needed locally.

### Framework-specific behaviour

`CURRENT_FRAMEWORK` controls which framework adapter is loaded at import time. The test suite must pass for all four supported frameworks. `make test` and `make test-cov` run all four automatically.

| Framework | Command | Skipped tests |
|-----------|---------|---------------|
| FastAPI   | `CURRENT_FRAMEWORK=fastapi make test` | 8 (Flask/Chalice/MCP-specific) |
| Flask     | `CURRENT_FRAMEWORK=flask make test`   | 9 (FastAPI/Chalice/MCP-specific) |
| Chalice   | `CURRENT_FRAMEWORK=chalice make test` | 17 (FastAPI/Flask/MCP-specific + Pydantic Request instantiation) |
| MCP       | `CURRENT_FRAMEWORK=mcp make test`     | 15 (FastAPI/Flask/Chalice-specific + Pydantic Request instantiation) |

`fastmcp` (the MCP server SDK) is a dev dependency and is installed automatically via `make install`. The MCP framework adapter test (`test_mcplib_framework_abstraction.py`) uses the real installed `fastmcp` package — no mocking of the `mcp` or `fastmcp` packages at module level (doing so would corrupt `mcp.server.lowlevel` for other tests).

Tests decorated with `@pytest.mark.skipif` are skipped gracefully — they are not failures. Framework-adapter test files (`test_fastapilib_*.py`, `test_flasklib_*.py`, `test_chalicelib_*.py`, `test_mcplib_*.py`) only run their real-SDK tests for the matching framework value. The shared `test_util_framework_abs_layer.py` imports from `{framework}lib.framework_abstraction` dynamically and skips Pydantic-specific instantiation tests when `CURRENT_FRAMEWORK=chalice` or `=mcp`.

### Coverage

`make test-cov` accumulates coverage across all four frameworks (using `--cov-append`) and runs a single final `coverage report --fail-under=30` on the combined result. This avoids the threshold firing on each individual framework run (each framework alone covers ~28-31%). The combined total is currently ~31%.

**Do not set `fail_under` in `.coveragerc`** — it would fire on every intermediate run and stop Make. The threshold is set only in the final `coverage report` call inside the `test-cov` Makefile target.

To raise the threshold as test coverage grows, update the `--fail-under=30` value in `Makefile`.

### Required environment variables for test runs

| Variable | Test value |
|----------|------------|
| `APP_NAME` | `test_app` |
| `APP_STAGE` | `test` |
| `APP_HOST_NAME` | `localhost` |
| `APP_SECRET_KEY` | `fake_secret_key` |
| `APP_SUPERADMIN_EMAIL` | `fake_email` |
| `GIT_SUBMODULE_LOCAL_PATH` | `fake_path` |
| `CLOUD_PROVIDER` | `aws` |
| `AWS_REGION` | `us-east-1` |
| `GET_SECRETS_ENABLED` | `0` |
| `APP_DB_URI` | `fake_db_uri` |
| `APP_DB_ENGINE` | `MONGODB` |
| `APP_DB_NAME` | `mongo` |
| `CURRENT_FRAMEWORK` | `fastapi` / `flask` / `chalice` / `mcp` |
| `STORAGE_URL_SEED` | `xyz` |

## Code style guidelines

- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for module-level constants, leading underscore for private methods (`_quote_identifier`, `_escape_sql_string_literal`).
- **Imports**: `typing` → stdlib → third-party → local `genericsuite.*`. No wildcard imports.
- **Type hints**: Required on all function signatures. Use `Optional`, `Union`, `Any` from `typing`. Return types always annotated.
- **Docstrings**: Triple-quoted with a one-line summary; include `Returns:` block when the shape is non-obvious.
- **Error returns**: All functions return a result dict `{'error': bool, 'error_message': str|None, 'resultset': dict|list}`. Use `get_default_resultset()` from `utilities.py` as the base. Never raise exceptions across module boundaries — catch and convert to error dict.
- **Error codes**: Tag every error message with a short positional code in brackets, e.g. `"_id is invalid [FUL3]"`. This makes log-grep easy.
- **Logging**: Use `log_debug` / `log_info` / `log_warning` / `log_error` from `app_logger.py`. Guard expensive debug calls with the module-level `DEBUG = False` flag using the walrus-operator idiom: `_ = DEBUG and log_debug(...)`.
- **Broad exceptions**: When catching `Exception` is unavoidable, suppress pylint with `# pylint: disable=broad-except` on the same line.
- **String formatting**: F-strings throughout. Multi-line strings use parenthesised concatenation, not backslash continuation.
- **Linting**: `pylint`, `flake8`, and `mypy` are all enforced. Per-file or per-line pylint disables (`C0103`, `R0902`, etc.) are acceptable when the rule conflicts with framework requirements; add a comment explaining why.

## Security considerations

- **No hardcoded secrets**: All credentials, keys, and URIs come from environment variables (`APP_SECRET_KEY`, `APP_DB_URI`, etc.) or cloud secret managers (AWS Secrets Manager, GCP Secret Manager, Azure KeyVault). The `GET_SECRETS_ENABLED=1` flag activates cloud-manager loading at startup via `config/config_secrets.py`.
- **Password hashing**: Passwords are hashed with `scrypt` (via Werkzeug `generate_password_hash`) salted with `APP_SECRET_KEY`. Never store or log plaintext passwords.
- **JWT tokens**: Signed with HS256 using `APP_SECRET_KEY`, expire in `EXPIRATION_MINUTES` (default 30 min). Expiry errors are caught and returned as 401 responses, not exceptions.
- **SQL injection prevention**: All SQL identifiers (table/column names) are quoted via `_quote_identifier()`. String literals are escaped via `_escape_sql_string_literal()`. `WHERE` clauses use parameterized placeholders (`%s`), never string interpolation of user values.
- **Log injection**: `sanitize_log_message()` in `app_logger.py` strips `\n` and `\r` from every log entry. Never log raw user input without sanitizing.
- **Debug logging**: Module-level `DEBUG = False` gates any log line that may contain sensitive runtime data (tokens, query results). Do not set `DEBUG = True` in committed code.
- **Input validation**: Use `verify_required_fields()` for mandatory field checks and `email_verification()` for email fields. Validate at system boundaries (HTTP request body, query params); trust internal data flow.
- **Authorization**: Group-based access control via `security.py`. All protected endpoints call `get_general_authorized_request()` to validate JWT before any data access. Superuser status is appended as the `admin` group, never stored as a boolean shortcut.
- **URL encryption**: Storage URLs can be encrypted with Fernet (`encryption.py`) when `STORAGE_URL_ENCRYPTION=1`. The seed comes from `STORAGE_URL_SEED` env var.
- **Secret caching**: Secrets fetched from cloud managers are cached to `TEMP_DIR` with obscured filenames (`s_ec_*`, `e_nv_*`). Ensure `TEMP_DIR` is not world-readable in production.

## Important Notes

- The files `AGENTS.md`, `GEMINI.md`, etc. (if present) have only a referece to `@CLAUDE.md` — edit only `CLAUDE.md`.
- Skills, commands, rules, and sub-agents are located in the `.claude/` directory.
