## 1. Dependencies

- [x] 1.1 Add `google-cloud-storage` and `google-cloud-secret-manager` as optional extras (`gcp`) in `pyproject.toml`
- [x] 1.2 Add `azure-storage-blob`, `azure-identity`, and `azure-keyvault-secrets` as optional extras (`azure`) in `pyproject.toml`
- [x] 1.3 Run `poetry lock` to update the lockfile
- [x] 1.4 Verify `make install` still succeeds and imports do not fail at startup

## 2. GCP Object Storage — `genericsuite/util/gcp.py`

- [x] 2.1 Add module-level constants: `DEBUG`, `CLOUD_STORAGE_PRESIGNED_ACTIVE` (mirroring `aws.py`)
- [x] 2.2 Implement `get_gcs_client()` with deferred `google.cloud.storage` import
- [x] 2.3 Implement `gcp_storage_base_url(bucket_name)` returning `https://storage.googleapis.com/{bucket_name}`
- [x] 2.4 Implement `get_bucket_key_from_url(public_url)` to parse `https://storage.googleapis.com/{bucket}/{key}`
- [x] 2.5 Implement `upload_file_to_storage(bucket_name, source_path, dest_path, public_file=False)` — upload blob, handle `FileNotFoundError` and credentials errors, return encrypted or plain URL
- [x] 2.6 Implement `remove_from_storage(bucket_name, key)` — delete blob, catch and return errors
- [x] 2.7 Implement `get_gcs_object(bucket_name, key)` — download blob bytes into `result['content']`
- [x] 2.8 Implement `download_gcs_object(bucket_name, key, local_file_path=None)` — use `temp_filename` when path is None
- [x] 2.9 Implement `get_gcs_presigned_url(bucket_name, object_key, expiration_seconds=None)` — v4 signed URL with `get_storage_presigned_expiration_seconds` default
- [x] 2.10 Fix `storage_retieval(item_id, other_params=None)` signature (remove `request` and `blueprint` args) and implement body mirroring `aws.py`
- [x] 2.11 Implement `prepare_asset_url(public_url)` respecting `CLOUD_STORAGE_PRESIGNED_ACTIVE` flag
- [x] 2.12 Remove unused imports (`Request`, `Any` from `framework_abs_layer`) added by the old stub

## 3. Azure Blob Storage — `genericsuite/util/azure.py`

- [x] 3.1 Add module-level constants: `DEBUG`, `CLOUD_STORAGE_PRESIGNED_ACTIVE`
- [x] 3.2 Implement `get_blob_service_client()` — try connection string first, fall back to account name + key; defer SDK imports
- [x] 3.3 Implement `blob_storage_base_url(bucket_name)` returning `https://{account}.blob.core.windows.net/{bucket_name}` (requires `AZURE_STORAGE_ACCOUNT_NAME`)
- [x] 3.4 Implement `get_bucket_key_from_url(public_url)` to parse `https://{account}.blob.core.windows.net/{container}/{key}`
- [x] 3.5 Implement `upload_file_to_storage(bucket_name, source_path, dest_path, public_file=False)` — upload blob, handle file-not-found and credential errors, return encrypted or plain URL
- [x] 3.6 Implement `remove_from_storage(bucket_name, key)` — delete blob, catch and return errors
- [x] 3.7 Implement `get_blob_object(bucket_name, key)` — download blob bytes into `result['content']`
- [x] 3.8 Implement `download_blob_object(bucket_name, key, local_file_path=None)` — use `temp_filename` when path is None
- [x] 3.9 Implement `get_blob_presigned_url(bucket_name, object_key, expiration_seconds=None)` — SAS token with `BlobSasPermissions(read=True)`, tagged error `GABPU-010` on failure
- [x] 3.10 Fix `storage_retieval(item_id, other_params=None)` signature and implement body mirroring `aws.py`
- [x] 3.11 Implement `prepare_asset_url(public_url)` respecting `CLOUD_STORAGE_PRESIGNED_ACTIVE` flag
- [x] 3.12 Remove unused imports (`Request`, `Any` from `framework_abs_layer`)

## 4. GCP Secrets Manager — `genericsuite/util/gcp_secrets.py`

- [x] 4.1 Implement `get_secrets(secret_name, region_name, get_default_resultset, logger)` using `google.cloud.secretmanager.SecretManagerServiceClient`; construct resource name from `GCP_PROJECT_ID`; parse JSON payload; tag errors `[G-GS-E010/020/030]`

## 5. Azure Key Vault — `genericsuite/util/azure_secrets.py`

- [x] 5.1 Implement `get_secrets(secret_name, region_name, get_default_resultset, logger)` using `azure.keyvault.secrets.SecretClient` + `azure.identity.DefaultAzureCredential`; read `AZURE_KEYVAULT_URL`; parse JSON value; tag errors `[AZ-GS-E010/020/030]`

## 6. Unit Tests

- [ ] 6.1 Create `tests/test_gcp_storage.py` — mock `google.cloud.storage.Client`; test `upload_file_to_storage`, `remove_from_storage`, `get_gcs_object`, `download_gcs_object`, `get_gcs_presigned_url`, `storage_retieval`, `prepare_asset_url`, `get_bucket_key_from_url`
- [ ] 6.2 Create `tests/test_azure_storage.py` — mock `azure.storage.blob.BlobServiceClient` and `generate_blob_sas`; test `upload_file_to_storage`, `remove_from_storage`, `get_blob_object`, `download_blob_object`, `get_blob_presigned_url`, `storage_retieval`, `prepare_asset_url`, `get_bucket_key_from_url`
- [ ] 6.3 Create `tests/test_gcp_secrets.py` — mock `google.cloud.secretmanager.SecretManagerServiceClient`; test `get_secrets` success, missing `GCP_PROJECT_ID`, GCP error, invalid JSON; test `get_cache_secret` cache-hit and cache-miss paths
- [ ] 6.4 Create `tests/test_azure_secrets.py` — mock `azure.keyvault.secrets.SecretClient`; test `get_secrets` success, missing `AZURE_KEYVAULT_URL`, AZ error, invalid JSON; test `get_cache_secret` cache-hit and cache-miss paths
- [ ] 6.5 Run `make test` and `make test-cov` and ensure all tests pass with no regressions

## 7. Documentation

- [ ] 7.1 Update `.env.example` with new env vars: `GCP_PROJECT_ID`, `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_ACCOUNT_KEY`, `AZURE_KEYVAULT_URL`
- [ ] 7.2 Update `CHANGELOG.md` with the new GCP and Azure storage capabilities
