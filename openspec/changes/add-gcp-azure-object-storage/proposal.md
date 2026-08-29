## Why

GCP and Azure object storage backends currently exist as stub implementations returning `"Not implemented"` errors. Any project deployed on GCP or Azure that tries to upload, retrieve, delete, or generate presigned URLs for files will fail at runtime. The AWS S3 implementation is complete and battle-tested; GCP (Cloud Storage) and Azure (Blob Storage) must reach parity so the `CLOUD_PROVIDER` environment variable can genuinely switch between all three clouds.

## What Changes

- **`genericsuite/util/gcp.py`** — Replace all stub bodies with real implementations using `google-cloud-storage`. Implement: `get_gcs_client`, `get_bucket_key_from_url`, `upload_file_to_storage`, `remove_from_storage`, `get_gcs_object`, `download_gcs_object`, `get_gcs_presigned_url`, `storage_retieval`, `prepare_asset_url`. Align signatures and return shapes with the AWS equivalents.
- **`genericsuite/util/azure.py`** — Replace all stub bodies with real implementations using `azure-storage-blob`. Implement: `get_blob_service_client`, `get_bucket_key_from_url`, `upload_file_to_storage`, `remove_from_storage`, `get_blob_object`, `download_blob_object`, `get_blob_presigned_url` (SAS token), `storage_retieval`, `prepare_asset_url`. Align signatures and return shapes with the AWS equivalents.
- **`genericsuite/util/gcp_secrets.py`** — Implement real GCP Secret Manager integration (currently returns an empty dict). Use `google-cloud-secret-manager`.
- **`genericsuite/util/azure_secrets.py`** — Implement real Azure Key Vault integration (currently returns an empty dict). Use `azure-keyvault-secrets` + `azure-identity`.
- **`pyproject.toml`** — Add `google-cloud-storage`, `google-cloud-secret-manager`, `azure-storage-blob`, `azure-identity`, `azure-keyvault-secrets` as optional dependencies (extras: `gcp`, `azure`).
- **`genericsuite/util/storage_commons.py`** — Adjust `get_storage_masked_url` to accept and pass the client object correctly for all providers (it currently takes an `s3_client` positional argument in `aws.py` but the signature only expects `bucket_name`, `key`).
- **Unit tests** — Add `tests/test_gcp_storage.py` and `tests/test_azure_storage.py` with mocked SDK calls, following the patterns in existing tests.

## Capabilities

### New Capabilities
- `gcp-object-storage`: Full GCP Cloud Storage CRUD, URL generation, presigned URL, and `prepare_asset_url` support, matching the AWS S3 feature set.
- `azure-object-storage`: Full Azure Blob Storage CRUD, URL generation, SAS-token presigned URL, and `prepare_asset_url` support, matching the AWS S3 feature set.
- `gcp-secrets-manager`: Real GCP Secret Manager integration for loading encrypted secrets and environment variables at startup.
- `azure-key-vault`: Real Azure Key Vault integration for loading encrypted secrets and environment variables at startup.

### Modified Capabilities
<!-- No existing specs to modify — all capabilities are new. -->

## Impact

- **`genericsuite/util/gcp.py`**, **`genericsuite/util/azure.py`**: Primary files being filled in.
- **`genericsuite/util/gcp_secrets.py`**, **`genericsuite/util/azure_secrets.py`**: Secrets modules being completed.
- **`genericsuite/util/storage.py`**: No structural changes needed; already routes to gcp/azure; stubs being replaced underneath.
- **`genericsuite/util/storage_commons.py`**: Minor signature correction to `get_storage_masked_url`.
- **`pyproject.toml`**: New optional dependency groups `gcp` and `azure`; no forced breakage for AWS-only consumers.
- **Tests**: New test files added; no existing tests modified.
- **Environment variables added**: `GCP_PROJECT_ID`, `GCP_STORAGE_BUCKET`, `AZURE_ACCOUNT_NAME`, `AZURE_ACCOUNT_KEY` (or `AZURE_CONNECTION_STRING`), `AZURE_KEYVAULT_URL`.
- **Dependencies**: `google-cloud-storage`, `google-cloud-secret-manager` (GCP extras); `azure-storage-blob`, `azure-identity`, `azure-keyvault-secrets` (Azure extras).
