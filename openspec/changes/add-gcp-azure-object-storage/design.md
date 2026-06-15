## Context

GenericSuite's storage layer (`genericsuite/util/storage.py`) is already wired to dispatch to three cloud providers (AWS, GCP, Azure) via `get_cloud_provider()`. The AWS S3 path is fully implemented in `aws.py`. The GCP and Azure paths in `gcp.py` and `azure.py` contain correct function signatures and docstrings but every body returns `error_resultset("Not implemented")` or raises `Exception("Not implemented")`.

Similarly, `gcp_secrets.py` and `azure_secrets.py` have the caching skeleton but `get_secrets()` returns an empty dict instead of calling the real cloud SDK.

Constraints:
- `cloud_provider_abstractor.py` must not import `config.py` or `app_context.py` (cycle guard, documented in the module).
- `gcp_secrets.py` and `azure_secrets.py` similarly cannot import from the broader app.
- All storage functions must return the same result-dict shape (`error`, `error_message`, `resultset`, plus provider-specific keys like `public_url`, `content`, `local_file_path`) used throughout the codebase.
- New cloud SDK imports must be deferred (inside functions) to keep the base install lightweight — the same pattern used by `aws.py` (`import boto3` inside `get_s3_client()`).
- The `storage_commons.get_storage_masked_url` function signature has already been corrected in the existing codebase (it no longer takes an `s3_client` arg); `aws.py` calls it as `get_storage_masked_url(bucket_name, dest_path)`.

## Goals / Non-Goals

**Goals:**
- Implement all functions in `gcp.py` using `google-cloud-storage` so `CLOUD_PROVIDER=GCP` works end-to-end.
- Implement all functions in `azure.py` using `azure-storage-blob` so `CLOUD_PROVIDER=AZURE` works end-to-end.
- Implement real secret fetching in `gcp_secrets.py` using `google-cloud-secret-manager`.
- Implement real secret fetching in `azure_secrets.py` using `azure-keyvault-secrets` + `azure-identity`.
- Add `gcp` and `azure` optional extras to `pyproject.toml`.
- Add unit tests with mocked SDKs for both providers.

**Non-Goals:**
- Changing `storage.py`, `cloud_provider_abstractor.py`, or any framework-specific endpoint code — the routing layer already works.
- Implementing multipart/resumable uploads or bucket lifecycle management.
- Supporting multiple storage accounts within one deployment.
- Changes to the AWS path.

## Decisions

### D1 — GCP: use `google-cloud-storage` client library

**Decision**: Use `google.cloud.storage.Client` for all GCP storage operations.

**Rationale**: The official Google Cloud Storage Python client is the standard way to interact with GCS buckets. It mirrors the boto3 pattern closely (client → bucket → blob), making the implementation straightforward to review alongside `aws.py`.

**Alternative considered**: Direct REST API calls via `google-auth` + `requests`. Rejected — more error-prone, more code, no pre-signed URL helper.

**Presigned URLs for GCS**: Use `blob.generate_signed_url(version="v4", expiration=timedelta(seconds=N), method="GET")`. This requires a service account key (JSON file path set via `GOOGLE_APPLICATION_CREDENTIALS`) or Workload Identity on GKE/Cloud Run. The same env-var convention is already used by the GCP secrets integration.

### D2 — Azure: use `azure-storage-blob` + SAS tokens for presigned URLs

**Decision**: Use `BlobServiceClient` from `azure-storage-blob` for all blob operations. Generate presigned URLs using `generate_blob_sas` with `BlobSasPermissions(read=True)`.

**Rationale**: `azure-storage-blob` is the official Azure Blob SDK. SAS tokens are the Azure equivalent of S3 presigned URLs — time-limited, signed access without exposing credentials.

**Authentication**: `BlobServiceClient` accepts a connection string (`AZURE_STORAGE_CONNECTION_STRING`) or an account name + key (`AZURE_STORAGE_ACCOUNT_NAME` + `AZURE_STORAGE_ACCOUNT_KEY`). The connection string is checked first; keys are the fallback.

**Alternative considered**: Azure SDK with DefaultAzureCredential (managed identity). Deferred to a follow-up — it adds complexity and may not be available in all deployment targets.

### D3 — GCP Secrets: `google-cloud-secret-manager`

**Decision**: Use `google.cloud.secretmanager.SecretManagerServiceClient` to access secrets by resource name `projects/{project_id}/secrets/{secret_name}/versions/latest`.

**Required env var**: `GCP_PROJECT_ID`. Without it, `get_secrets()` returns an error resultset.

### D4 — Azure Secrets: `azure-keyvault-secrets` + `azure-identity`

**Decision**: Use `SecretClient` from `azure-keyvault-secrets` with `DefaultAzureCredential` from `azure-identity`.

**Required env var**: `AZURE_KEYVAULT_URL` (e.g., `https://<vault>.vault.azure.net`). Credentials are supplied by `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` (service principal) or via managed identity in Azure environments.

### D5 — Optional extras in `pyproject.toml`

**Decision**: Add `gcp = ["google-cloud-storage", "google-cloud-secret-manager"]` and `azure = ["azure-storage-blob", "azure-identity", "azure-keyvault-secrets"]` as optional dependency groups.

**Rationale**: Keeps the base install slim. AWS-only deployments do not need 150 MB of GCP/Azure SDKs.

### D6 — Lazy imports (inside functions)

**Decision**: All cloud SDK imports (`google.cloud.storage`, `azure.storage.blob`, etc.) are placed inside the function body that uses them, not at module top level.

**Rationale**: Mirrors the `aws.py` pattern (`import boto3` inside `get_s3_client()`). Prevents `ImportError` on startup for deployments that don't have the optional extras installed.

### D7 — `storage_retieval` signature

The existing stub signatures in `gcp.py` and `azure.py` incorrectly include `request: Request` and `blueprint: Any` parameters that the AWS implementation and `storage.py` dispatcher do not pass. These will be corrected to match the AWS signature: `storage_retieval(item_id, other_params=None)`.

## Risks / Trade-offs

- **GCS signed URLs require service account credentials** → Projects using Workload Identity (no key file) will need to use `iam.serviceAccounts.signBlob` permission. Mitigation: document the `GOOGLE_APPLICATION_CREDENTIALS` requirement; return a clear error if signing fails.
- **Azure SAS token generation requires the account key** → If only managed identity is available, SAS tokens cannot be generated without an extra `UserDelegationKey` call. Mitigation: attempt account-key path first; log a clear error if key is absent.
- **Presigned URL feature flag** (`CLOUD_STORAGE_PRESIGNED_ACTIVE`) is already respected in `aws.py`. GCP and Azure implementations must honour it too to avoid exposing private blobs unexpectedly.
- **Test coverage**: SDK calls will be mocked with `unittest.mock.patch`; real cloud connectivity is not tested in CI. Mitigation: integration test instructions documented in comments.

## Migration Plan

1. Install the relevant extras: `poetry add --optional google-cloud-storage google-cloud-secret-manager` and `poetry add --optional azure-storage-blob azure-identity azure-keyvault-secrets`.
2. Set required env vars (`GCP_PROJECT_ID` for GCP; `AZURE_STORAGE_CONNECTION_STRING` or `AZURE_STORAGE_ACCOUNT_NAME`+`AZURE_STORAGE_ACCOUNT_KEY` for Azure).
3. Set `CLOUD_PROVIDER=GCP` or `CLOUD_PROVIDER=AZURE` and run the application.
4. No data migration — no schema changes, no existing AWS data affected.
5. Rollback: revert `gcp.py` / `azure.py` to stubs (or set `CLOUD_PROVIDER=AWS`).

## Open Questions

- Should `prepare_asset_url` for GCP/Azure also support the `CLOUD_STORAGE_PRESIGNED_ACTIVE=0` path (return public URL directly)? **Working assumption**: yes — mirrors the AWS behaviour.
- Should the `azure_secrets.py` implementation support both Key Vault secrets (key-value pairs) and environment-style blobs stored as secrets? **Working assumption**: same two-set pattern as AWS (`{app}-{stage}-secrets` for encrypted secrets, `{app}-{stage}-envs` for plain env vars), matching the existing `get_cache_secret` skeleton.
