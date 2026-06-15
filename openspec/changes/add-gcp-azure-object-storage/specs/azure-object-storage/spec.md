## ADDED Requirements

### Requirement: Azure Blob Service client initialisation
The system SHALL provide a `get_blob_service_client()` function in `genericsuite/util/azure.py` that returns an `azure.storage.blob.BlobServiceClient`. It SHALL first attempt to use `AZURE_STORAGE_CONNECTION_STRING`; if not set, it SHALL construct the client from `AZURE_STORAGE_ACCOUNT_NAME` and `AZURE_STORAGE_ACCOUNT_KEY`. All SDK imports SHALL be deferred inside the function.

#### Scenario: Client via connection string
- **WHEN** `AZURE_STORAGE_CONNECTION_STRING` is set
- **THEN** a `BlobServiceClient` created from the connection string is returned

#### Scenario: Client via account name and key
- **WHEN** `AZURE_STORAGE_CONNECTION_STRING` is absent and `AZURE_STORAGE_ACCOUNT_NAME` + `AZURE_STORAGE_ACCOUNT_KEY` are set
- **THEN** a `BlobServiceClient` constructed from account URL and key is returned

#### Scenario: Missing credentials
- **WHEN** neither connection string nor account name/key are available
- **THEN** the calling function catches the resulting exception and returns an error resultset

---

### Requirement: Upload file to Azure Blob Storage
The system SHALL implement `upload_file_to_storage(bucket_name, source_path, dest_path, public_file=False)` in `genericsuite/util/azure.py`. `bucket_name` maps to the Azure container name. On success it SHALL return a result dict with `public_url`, `final_filename`, `error=False`, and `error_message=None`. When `storage_url_encryption_enabled()` is True it SHALL return an encrypted masked URL; otherwise `https://{account_name}.blob.core.windows.net/{bucket_name}/{dest_path}`.

#### Scenario: Successful upload, encryption disabled
- **WHEN** a valid file is uploaded and `storage_url_encryption_enabled()` returns False
- **THEN** `error=False` and `public_url` is of the form `https://{account}.blob.core.windows.net/{container}/{dest_path}`

#### Scenario: Successful upload, encryption enabled
- **WHEN** `storage_url_encryption_enabled()` returns True
- **THEN** `public_url` is the value returned by `get_storage_masked_url(bucket_name, dest_path)`

#### Scenario: Source file not found
- **WHEN** `source_path` does not exist
- **THEN** `error=True` and `error_message` describes the missing file

#### Scenario: Container not found
- **WHEN** the container `bucket_name` does not exist in the storage account
- **THEN** `error=True` and `error_message` describes the failure

---

### Requirement: Remove object from Azure Blob Storage
The system SHALL implement `remove_from_storage(bucket_name, key)` that deletes the blob at `key` within container `bucket_name`.

#### Scenario: Successful deletion
- **WHEN** the blob exists and credentials are valid
- **THEN** the blob is deleted and `error=False`

#### Scenario: Blob not found
- **WHEN** the blob does not exist
- **THEN** `error=True` and `error_message` describes the failure

---

### Requirement: Get Azure blob content
The system SHALL implement `get_blob_object(bucket_name, key)` that downloads and returns blob bytes in `result['content']`.

#### Scenario: Successful retrieval
- **WHEN** the blob exists
- **THEN** `result['content']` contains the raw bytes and `error=False`

#### Scenario: Blob not found
- **WHEN** the blob does not exist
- **THEN** `error=True` and `error_message` describes the failure

---

### Requirement: Download Azure blob to temp file
The system SHALL implement `download_blob_object(bucket_name, key, local_file_path=None)`. When `local_file_path` is None it SHALL generate a temp path via `temp_filename`. On success it SHALL set `result['local_file_path']`.

#### Scenario: Download with auto temp path
- **WHEN** `local_file_path` is None
- **THEN** the blob is saved to an auto-generated path and `result['local_file_path']` is set

#### Scenario: Download to explicit path
- **WHEN** `local_file_path` is provided
- **THEN** the blob is saved to that path and `result['local_file_path']` equals the provided path

---

### Requirement: Generate Azure Blob SAS presigned URL
The system SHALL implement `get_blob_presigned_url(bucket_name, object_key, expiration_seconds=None)` using `generate_blob_sas` with `BlobSasPermissions(read=True)`. The expiry SHALL default to `get_storage_presigned_expiration_seconds()`. The result SHALL contain `url` on success.

#### Scenario: SAS URL generated
- **WHEN** `AZURE_STORAGE_ACCOUNT_NAME` and `AZURE_STORAGE_ACCOUNT_KEY` are set and the blob exists
- **THEN** `result['url']` contains a SAS-signed URL and `error=False`

#### Scenario: Missing account key
- **WHEN** `AZURE_STORAGE_ACCOUNT_KEY` is absent (managed identity only environment)
- **THEN** `error=True` and `error_message` is tagged `GABPU-010`

---

### Requirement: Azure Blob storage retrieval from encrypted item_id
The system SHALL implement `storage_retieval(item_id, other_params=None)` matching the AWS signature. It SHALL decrypt `item_id`, then call `get_blob_object` or `download_blob_object` based on `other_params['mode']`. It SHALL populate `mime_type` and `filename` on the result.

#### Scenario: Successful retrieval in get mode
- **WHEN** `item_id` decrypts to a valid container/key pair and mode is `'get'`
- **THEN** `result['content']`, `result['mime_type']`, and `result['filename']` are populated

#### Scenario: Missing item_id
- **WHEN** `item_id` is None or empty
- **THEN** `error=True` and `error_message` is tagged `AZSR-E1010`

---

### Requirement: Prepare Azure Blob asset URL for AI tools
The system SHALL implement `prepare_asset_url(public_url)` in `genericsuite/util/azure.py`. When `CLOUD_STORAGE_PRESIGNED_ACTIVE=1` it SHALL call `get_blob_presigned_url` and return the SAS URL. When `CLOUD_STORAGE_PRESIGNED_ACTIVE=0` it SHALL return `public_url` unchanged.

#### Scenario: SAS URL returned when feature active
- **WHEN** `CLOUD_STORAGE_PRESIGNED_ACTIVE=1` and SAS generation succeeds
- **THEN** the returned URL is a time-limited SAS URL

#### Scenario: Public URL returned when feature inactive
- **WHEN** `CLOUD_STORAGE_PRESIGNED_ACTIVE=0`
- **THEN** the original `public_url` is returned unchanged

---

### Requirement: Parse container name and key from Azure Blob public URL
The system SHALL implement `get_bucket_key_from_url(public_url)` that parses the container name and blob key from a `https://{account}.blob.core.windows.net/{container}/{key}` URL.

#### Scenario: Valid Azure Blob URL parsed
- **WHEN** a URL of the form `https://myaccount.blob.core.windows.net/mycontainer/path/to/file.jpg` is provided
- **THEN** the function returns `("mycontainer", "path/to/file.jpg")`
