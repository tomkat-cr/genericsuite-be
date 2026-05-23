## Context

The `genericsuite-be` library has ~80 source modules across `config/`, `util/`, `models/`, `constants/`, and four framework adapters (`fastapilib/`, `flasklib/`, `chalicelib/`, `mcplib/`). Existing tests (6 files, ~1,900 lines) cover only DB abstractor operator translation. All other modules — including config, security, JWT, passwords, encryption, CRUD helpers, and framework adapters — have zero test coverage.

The test framework (pytest) and runner (`make test`) are already set up via `pyproject.toml`. No live database or cloud account is available during test runs.

## Goals / Non-Goals

**Goals:**
- Add pytest unit tests for every public function and class in `genericsuite/`
- All tests run with no live external services (DB, cloud, SMTP) — all mocked
- Shared fixtures in `tests/conftest.py` eliminate boilerplate across test files
- `pytest-cov` integration generates coverage reports; `make test-cov` enforces ≥80% coverage
- Each new test file mirrors its source module path (e.g., `tests/test_util_jwt.py`)

**Non-Goals:**
- Integration or end-to-end tests against real databases or cloud APIs
- Tests for the `genericsuite-be-ai` package (separate repo)
- 100% branch coverage on every module (80% minimum; complex adapter glue code may stay lower)
- Changes to any production source file

## Decisions

### 1. One test file per source module

**Decision**: `tests/test_<module_path>.py` mirrors `genericsuite/<module_path>.py` (underscores replace slashes).

**Rationale**: Easy to locate the test for any source file. Consistent with the existing naming pattern (`test_db_abstractor_*.py`). Alternative (grouping by capability) was rejected because it obscures which functions lack coverage.

### 2. All external dependencies mocked via `unittest.mock` / `pytest-mock`

**Decision**: Use `pytest-mock` (`mocker` fixture) and `unittest.mock.patch` for all external calls — boto3, pymongo, psycopg2, SQLAlchemy sessions, SMTP, filesystem writes, cloud secret managers.

**Rationale**: `make test` must run offline in CI with no credentials. The existing DB abstractor tests already use this pattern (`MagicMock`), so continuing it is consistent. True integration tests are not in scope.

### 3. Shared `conftest.py` for environment and Config fixtures

**Decision**: `tests/conftest.py` defines:
- `set_env` autouse fixture — sets all required env vars (`APP_NAME`, `APP_STAGE=test`, `APP_SECRET_KEY`, etc.)
- `mock_config` fixture — returns a `Config` instance with test values
- `mock_db` fixture — returns a `MagicMock` that passes as a DB abstractor
- `mock_request` fixture — returns a minimal framework-agnostic `Request` object

**Rationale**: Avoids 40+ test files each duplicating the same 15 env-var setup lines. Already implied by how the existing `make test` command injects vars on the command line.

### 4. Test grouping by capability, spec per capability

**Decision**: Seven spec files map directly to the seven capability groups defined in the proposal. Tasks are generated per spec.

**Rationale**: Keeps each spec focused and reviewable. Avoids one monolithic spec file that is hard to track.

### 5. `pytest-cov` as dev dependency, not a new CI system

**Decision**: Add `pytest-cov` and `pytest-mock` to `[tool.poetry.dev-dependencies]` in `pyproject.toml`. Add `make test-cov` target that runs `pytest --cov=genericsuite --cov-fail-under=80`.

**Rationale**: Minimal infrastructure change. Does not require a new CI pipeline job — the existing `make test` path is unchanged.

## Risks / Trade-offs

- [Framework adapter tests are thin] FastAPI/Flask/Chalice/MCP framework adapters require importing the framework at test time. Some adapters may have optional imports guarded at runtime. → Mitigation: test only the `framework_abstraction.py` logic layer and mock the framework's `Request`/`Response` objects; skip framework-level routing tests.
- [Config class reads env vars at import time] Patching env vars after import may miss early bindings. → Mitigation: use `importlib.reload` or `monkeypatch.setenv` before importing Config in each test; centralise in `conftest.py`.
- [Cloud provider helpers have heavy SDK imports] `boto3`, `azure-identity`, `google-cloud-*` may not all be installed in a minimal test environment. → Mitigation: mock the SDK modules at the top of each cloud test file using `sys.modules` patching; test only the logic that wraps those SDKs.
- [Coverage gap on complex glue code] Some adapter files are largely pass-through wiring. Reaching 80% there may require significant mock setup with low ROI. → Mitigation: exclude those files from the coverage threshold using `.coveragerc` per-file exclusions; document the exclusion.

## Migration Plan

1. Add `pytest-cov` and `pytest-mock` to `pyproject.toml` dev deps → run `poetry install`
2. Create `tests/conftest.py` with shared fixtures
3. Implement test files capability-by-capability in the order defined in `tasks.md`
4. Add `make test-cov` target to `Makefile`
5. Add `.coveragerc` to configure omit paths (e.g., `genericsuite/*/endpoints/__init__.py`)
6. All existing tests (`make test`) must remain green throughout

## Open Questions

- Should `tests/conftest.py` use `pytest-dotenv` to load a `tests/.env.test` file, or keep injecting vars directly via `monkeypatch`? (Current approach: `monkeypatch` / autouse fixture — simpler, no extra dependency.)
- What is the minimum acceptable coverage per module for framework adapters? (Proposed: 60% for adapter glue code, 80% global.)
