## ADDED Requirements

### Requirement: security module validates JWT and enforces group membership
`security.py` SHALL provide `get_general_authorized_request()` that validates the bearer token, decodes the JWT, and returns a result dict containing the user context. Requests with invalid or missing tokens SHALL return `error == True`.

#### Scenario: Valid JWT yields authorized user context
- **WHEN** a request with a valid bearer token is passed to `get_general_authorized_request()`
- **THEN** the result has `error == False` and `resultset` contains the user's group list

#### Scenario: Missing token returns unauthorized error
- **WHEN** a request with no Authorization header is passed
- **THEN** the result has `error == True` and a 401-equivalent error message

#### Scenario: Expired JWT returns unauthorized error
- **WHEN** a request carries an expired token
- **THEN** the result has `error == True` and `error_message` references token expiry

#### Scenario: Superadmin email grants admin group membership
- **WHEN** the JWT sub equals `APP_SUPERADMIN_EMAIL`
- **THEN** the result's user context includes `"admin"` in the group list

### Requirement: app_context derives safe identifiers from user_id
`app_context.py` SHALL sanitize `user_id` values so that characters not allowed in filenames (slashes, null bytes, path separators) are removed or replaced before use in file-path construction.

#### Scenario: Valid ObjectId passes through unchanged
- **WHEN** a valid 24-hex-char `user_id` is processed
- **THEN** the resulting identifier equals the input

#### Scenario: Path-traversal characters are removed
- **WHEN** `user_id` contains `../` or null bytes
- **THEN** the resulting identifier contains neither `../` nor `\0`

### Requirement: current_user_data returns user document from DB
`current_user_data.py` SHALL retrieve the current user's document from the database using the decoded JWT subject and return it in the standard result dict. DB failures SHALL be surfaced as error results, not exceptions.

#### Scenario: User found in DB
- **WHEN** the JWT subject matches a user document in the mocked DB
- **THEN** `resultset` contains the user document and `error == False`

#### Scenario: User not found in DB
- **WHEN** the mocked DB returns an empty result
- **THEN** `error == True` and `error_message` is non-empty

#### Scenario: DB raises exception
- **WHEN** the mocked DB raises a runtime exception
- **THEN** `error == True` and no exception propagates to the caller
