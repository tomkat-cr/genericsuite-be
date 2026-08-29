## ADDED Requirements

### Requirement: Fetch secret from Azure Key Vault
The system SHALL implement `get_secrets(secret_name, region_name, get_default_resultset, logger)` in `genericsuite/util/azure_secrets.py` that retrieves a secret from Azure Key Vault using `azure.keyvault.secrets.SecretClient` and `azure.identity.DefaultAzureCredential`. The Key Vault URL SHALL come from the `AZURE_KEYVAULT_URL` environment variable. The import SHALL be deferred inside the function.

#### Scenario: Secret retrieved successfully
- **WHEN** `AZURE_KEYVAULT_URL` is set and the named secret exists in the Key Vault
- **THEN** `result['resultset']` contains the parsed JSON dict of the secret value and `error=False`

#### Scenario: Missing AZURE_KEYVAULT_URL
- **WHEN** the `AZURE_KEYVAULT_URL` environment variable is not set
- **THEN** `error=True` and `error_message` is tagged `[AZ-GS-E010]`

#### Scenario: Secret not found in Key Vault
- **WHEN** the secret name does not exist or credentials are invalid
- **THEN** `error=True` and `error_message` contains the Azure SDK error tagged `[AZ-GS-E020]`

#### Scenario: Secret value is not valid JSON
- **WHEN** the secret value cannot be parsed as JSON
- **THEN** `error=True` and `error_message` is tagged `[AZ-GS-E030]`

---

### Requirement: Azure secrets cache integrates with Key Vault
The system SHALL ensure `get_cache_secret` in `azure_secrets.py` stores secrets fetched from Azure Key Vault into the cache file and loads from cache on subsequent calls. The cache file structure (`{TEMP_DIR}/s_ec_{app}_{stage}_azure.json` and `{TEMP_DIR}/e_nv_{app}_{stage}_azure.json`) SHALL remain unchanged.

#### Scenario: Cache miss — fetches from Azure Key Vault
- **WHEN** the cache file does not exist and `GET_SECRETS_CRITICAL=1`
- **THEN** `get_secrets` is called, the result is written to the appropriate cache file, and the secrets are returned

#### Scenario: Cache hit — skips Key Vault call
- **WHEN** the cache file already exists
- **THEN** secrets are read from the cache file without calling Azure Key Vault
