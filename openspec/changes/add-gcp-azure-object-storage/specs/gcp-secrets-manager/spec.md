## ADDED Requirements

### Requirement: Fetch secret from GCP Secret Manager
The system SHALL implement `get_secrets(secret_name, region_name, get_default_resultset, logger)` in `genericsuite/util/gcp_secrets.py` that retrieves the latest version of a secret from GCP Secret Manager using `google.cloud.secretmanager.SecretManagerServiceClient`. The secret resource name SHALL be constructed as `projects/{GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest`. The import SHALL be deferred inside the function.

#### Scenario: Secret retrieved successfully
- **WHEN** `GCP_PROJECT_ID` is set and the secret exists in GCP Secret Manager
- **THEN** `result['resultset']` contains the parsed JSON dict of the secret value and `error=False`

#### Scenario: Missing GCP_PROJECT_ID
- **WHEN** the `GCP_PROJECT_ID` environment variable is not set
- **THEN** `error=True` and `error_message` is tagged `[G-GS-E010]`

#### Scenario: Secret not found in GCP
- **WHEN** the secret name does not exist or credentials are invalid
- **THEN** `error=True` and `error_message` contains the GCP API error tagged `[G-GS-E020]`

#### Scenario: Secret value is not valid JSON
- **WHEN** the secret payload cannot be parsed as JSON
- **THEN** `error=True` and `error_message` is tagged `[G-GS-E030]`

---

### Requirement: GCP secrets cache integrates with Secret Manager
The system SHALL ensure `get_cache_secret` in `gcp_secrets.py` actually stores secrets fetched from GCP Secret Manager into the cache file, and loads from cache on subsequent calls. The existing cache file logic (`secrets_cache_filename`) SHALL remain unchanged in structure.

#### Scenario: Cache miss — fetches from GCP
- **WHEN** the cache file does not exist and `GET_SECRETS_CRITICAL=1`
- **THEN** `get_secrets` is called, the result is written to `{TEMP_DIR}/s_ec_{app}_{stage}_gcp.json`, and the secrets are returned

#### Scenario: Cache hit — skips GCP call
- **WHEN** the cache file already exists
- **THEN** secrets are read from the cache file without calling GCP Secret Manager
