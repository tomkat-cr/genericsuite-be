## ADDED Requirements

### Requirement: GCS client initialisation
The system SHALL provide a `get_gcs_client()` function in `genericsuite/util/gcp.py` that returns a `google.cloud.storage.Client` instance. The import of `google.cloud.storage` SHALL be deferred inside the function body.

#### Scenario: Client created successfully
- **WHEN** `get_gcs_client()` is called with valid application credentials available
- **THEN** a `google.cloud.storage.Client` instance is returned without error

#### Scenario: Missing credentials
- **WHEN** no `GOOGLE_APPLICATION_CREDENTIALS` or ADC credential is present
- **THEN** the calling function catches the resulting exception and returns an error resultset with a descriptive message

---

### Requirement: Upload file to GCS bucket
The system SHALL implement `upload_file_to_storage(bucket_name, source_path, dest_path, public_file=False)` in `genericsuite/util/gcp.py`. On success it SHALL return a result dict containing `public_url`, `final_filename`, `error=False`, and `error_message=None`. When `storage_url_encryption_enabled()` is True it SHALL return an encrypted masked URL; otherwise it SHALL return `https://storage.googleapis.com/{bucket_name}/{dest_path}`.

#### Scenario: Successful upload, encryption disabled
- **WHEN** a valid file at `source_path` is uploaded with `storage_url_encryption_enabled()` returning False
- **THEN** the result contains `error=False` and `public_url` of the form `https://storage.googleapis.com/{bucket_name}/{dest_path}`

#### Scenario: Successful upload, encryption enabled
- **WHEN** `storage_url_encryption_enabled()` returns True
- **THEN** `public_url` is the value returned by `get_storage_masked_url(bucket_name, dest_path)`

#### Scenario: Source file not found
- **WHEN** `source_path` does not exist
- **THEN** `error=True` and `error_message` contains a descriptive message

#### Scenario: Missing credentials during upload
- **WHEN** no valid GCS credentials are configured
- **THEN** `error=True` and `error_message` contains a descriptive message

---

### Requirement: Remove object from GCS bucket
The system SHALL implement `remove_from_storage(bucket_name, key)` in `genericsuite/util/gcp.py` that deletes the blob at `key` in `bucket_name`. On failure it SHALL return an error resultset.

#### Scenario: Successful deletion
- **WHEN** the blob exists and credentials are valid
- **THEN** the blob is deleted and the result has `error=False`

#### Scenario: Blob not found
- **WHEN** the specified blob does not exist
- **THEN** the result has `error=True` and `error_message` describes the failure

---

### Requirement: Get GCS object content
The system SHALL implement `get_gcs_object(bucket_name, key)` that downloads and returns the raw bytes of the object in the `content` field of the result dict.

#### Scenario: Successful retrieval
- **WHEN** the blob exists
- **THEN** `result['content']` contains the raw bytes of the object and `error=False`

#### Scenario: Object not found
- **WHEN** the blob does not exist
- **THEN** `error=True` and `error_message` describes the failure

---

### Requirement: Download GCS object to temp file
The system SHALL implement `download_gcs_object(bucket_name, key, local_file_path=None)`. When `local_file_path` is None it SHALL generate a temp path via `temp_filename`. On success it SHALL set `result['local_file_path']` to the downloaded path.

#### Scenario: Download with auto temp path
- **WHEN** `local_file_path` is None
- **THEN** the blob is downloaded to an auto-generated temp path and `result['local_file_path']` is set

#### Scenario: Download to explicit path
- **WHEN** `local_file_path` is provided
- **THEN** the blob is downloaded to that path and `result['local_file_path']` equals the provided path

---

### Requirement: Generate GCS presigned URL
The system SHALL implement `get_gcs_presigned_url(bucket_name, object_key, expiration_seconds=None)` that returns a signed URL valid for `expiration_seconds` (defaulting to `get_storage_presigned_expiration_seconds()`). The result SHALL contain `url` on success.

#### Scenario: Presigned URL generated
- **WHEN** valid credentials are available and the object exists
- **THEN** `result['url']` contains a time-limited signed URL and `error=False`

#### Scenario: Signing failure
- **WHEN** the service account lacks `iam.serviceAccounts.signBlob` permission
- **THEN** `error=True` and `error_message` contains a descriptive message tagged with error code `GGPSU-010`

---

### Requirement: GCS storage retrieval from encrypted item_id
The system SHALL implement `storage_retieval(item_id, other_params=None)` in `genericsuite/util/gcp.py` matching the signature of the AWS equivalent. It SHALL decrypt `item_id` using `get_bucket_key_from_decripted_item_id`, then call `get_gcs_object` (mode `get`) or `download_gcs_object` (mode `download`). It SHALL populate `mime_type` and `filename` on the result.

#### Scenario: Successful retrieval in get mode
- **WHEN** `item_id` decrypts to a valid bucket/key pair and `other_params['mode']` is `'get'`
- **THEN** `result['content']`, `result['mime_type']`, and `result['filename']` are populated

#### Scenario: Missing item_id
- **WHEN** `item_id` is None or empty
- **THEN** `error=True` and `error_message` is tagged `GSR-E1010`

---

### Requirement: Prepare GCS asset URL for AI tools
The system SHALL implement `prepare_asset_url(public_url)` in `genericsuite/util/gcp.py`. When `CLOUD_STORAGE_PRESIGNED_ACTIVE=1`, it SHALL call `get_gcs_presigned_url` and return the signed URL. When `CLOUD_STORAGE_PRESIGNED_ACTIVE=0`, it SHALL return `public_url` unchanged.

#### Scenario: Presigned URL returned when feature active
- **WHEN** `CLOUD_STORAGE_PRESIGNED_ACTIVE=1` and signing succeeds
- **THEN** the returned URL is a time-limited signed URL

#### Scenario: Public URL returned when feature inactive
- **WHEN** `CLOUD_STORAGE_PRESIGNED_ACTIVE=0`
- **THEN** the original `public_url` is returned unchanged

---

### Requirement: Parse bucket name and key from GCS public URL
The system SHALL implement `get_bucket_key_from_url(public_url)` that extracts the bucket name and object key from a `https://storage.googleapis.com/{bucket}/{key}` URL.

#### Scenario: Valid GCS URL parsed
- **WHEN** a URL of the form `https://storage.googleapis.com/my-bucket/path/to/file.jpg` is provided
- **THEN** the function returns `("my-bucket", "path/to/file.jpg")`
