## ADDED Requirements

### Requirement: storage module uploads and retrieves files via mocked cloud SDK
`util/storage.py` SHALL provide upload and retrieval functions that delegate to the active cloud provider. All cloud SDK calls SHALL be replaced by mocks in tests; the test SHALL verify the delegation logic, not the SDK itself.

#### Scenario: Upload delegates to the configured provider
- **WHEN** `storage.upload(file_content, filename)` is called with `CLOUD_PROVIDER=aws`
- **THEN** the AWS S3 put-object mock is called exactly once with the expected bucket and key

#### Scenario: Retrieval returns a URL string on success
- **WHEN** `storage.get_url(filename)` is called and the cloud mock returns a URL
- **THEN** the function returns a non-empty string

#### Scenario: Upload failure returns error result
- **WHEN** the cloud SDK mock raises an exception
- **THEN** `error == True` and no exception propagates to the caller

### Requirement: cloud_provider_abstractor selects correct backend from CLOUD_PROVIDER env var
`util/cloud_provider_abstractor.py` SHALL use the `ObjectFactory` pattern to return an AWS, Azure, or GCP provider instance based on `CLOUD_PROVIDER`. The factory SHALL be testable by patching the SDK modules.

#### Scenario: CLOUD_PROVIDER=aws returns AWS provider
- **WHEN** `CLOUD_PROVIDER=aws` and the factory is invoked
- **THEN** the returned object is an instance of the AWS provider class

#### Scenario: CLOUD_PROVIDER=gcp returns GCP provider
- **WHEN** `CLOUD_PROVIDER=gcp` and the factory is invoked
- **THEN** the returned object is an instance of the GCP provider class

#### Scenario: Unsupported CLOUD_PROVIDER returns error or raises
- **WHEN** `CLOUD_PROVIDER=unknown` and the factory is invoked
- **THEN** an error result is returned or a descriptive exception is raised

### Requirement: aws helper functions wrap boto3 with error handling
`util/aws.py` SHALL wrap boto3 calls (S3, Secrets Manager, etc.) in try/except blocks and return standard error result dicts on failure.

#### Scenario: S3 get_object returns content on success
- **WHEN** boto3 `get_object` mock returns a successful response
- **THEN** the helper returns `error == False` and `resultset` contains the file content

#### Scenario: S3 get_object ClientError returns error result
- **WHEN** boto3 `get_object` raises `botocore.exceptions.ClientError`
- **THEN** the helper returns `error == True` and `error_message` is non-empty

### Requirement: aws_secrets / azure_secrets / gcp_secrets modules are testable with mocked SDKs
Each secrets helper (aws_secrets.py, azure_secrets.py, gcp_secrets.py) SHALL expose a `get_secret(name)` function. All SDK-specific imports SHALL be patchable via `sys.modules` to avoid requiring installed SDKs in the test environment.

#### Scenario: AWS secrets returns value when Secrets Manager responds
- **WHEN** `boto3.client("secretsmanager").get_secret_value` is mocked to return a value
- **THEN** `aws_secrets.get_secret("my-secret")` returns that value

#### Scenario: Azure secrets returns value when KeyVault client responds
- **WHEN** the Azure `SecretClient.get_secret` mock returns a value
- **THEN** `azure_secrets.get_secret("my-secret")` returns that value

#### Scenario: GCP secrets returns value when Secret Manager client responds
- **WHEN** the GCP `SecretManagerServiceClient.access_secret_version` mock returns a payload
- **THEN** `gcp_secrets.get_secret("my-secret")` returns the decoded payload

### Requirement: storage_commons provides shared constants and helpers
`util/storage_commons.py` SHALL expose helper functions for building storage keys and validating allowed file extensions that return predictable output for known inputs.

#### Scenario: Storage key is built from user_id and filename
- **WHEN** `build_storage_key(user_id="u1", filename="photo.jpg")` is called
- **THEN** the returned key contains both `u1` and `photo.jpg`

#### Scenario: Disallowed extension is rejected
- **WHEN** a filename with a disallowed extension is validated
- **THEN** the validation function returns `error == True`

#### Scenario: Allowed extension passes validation
- **WHEN** a filename with an allowed extension (e.g., `.jpg`) is validated
- **THEN** the validation function returns `error == False`
