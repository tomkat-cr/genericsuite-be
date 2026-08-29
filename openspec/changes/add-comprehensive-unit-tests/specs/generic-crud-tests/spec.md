## ADDED Requirements

### Requirement: GenericDbHelper builds correct filters from JSON config
`GenericDbHelper` SHALL translate JSON field definitions into database query filters. Given a mock DB abstractor, `find_by_id()` SHALL call the abstractor with the correctly structured query.

#### Scenario: find_by_id calls abstractor with _id filter
- **WHEN** `find_by_id("abc123")` is called on a `GenericDbHelper` with a mocked DB
- **THEN** the DB abstractor's `find_one` is called with `{"_id": "abc123"}` or equivalent

#### Scenario: list_all passes projection derived from JSON config
- **WHEN** `list_all()` is called
- **THEN** the DB abstractor's `find` receives a projection that includes only the fields listed in the JSON config

#### Scenario: create_item returns new document on success
- **WHEN** the mocked DB abstractor returns a successful insert result
- **THEN** `create_item()` returns `error == False` and `resultset` contains the created document

#### Scenario: create_item returns error on DB failure
- **WHEN** the mocked DB abstractor raises an exception during insert
- **THEN** `create_item()` returns `error == True` and `error_message` is non-empty

### Requirement: GenericDbHelperSuper enforces required field validation before DB write
`GenericDbHelperSuper` SHALL call `verify_required_fields()` before any create or update operation. Missing required fields SHALL prevent the DB call and return an error result.

#### Scenario: Missing required field blocks DB write
- **WHEN** a create call omits a field marked as required in the JSON config
- **THEN** `error == True`, `error_message` names the missing field, and no DB call is made

#### Scenario: All required fields present allows DB write
- **WHEN** all required fields are present in the payload
- **THEN** the DB abstractor's insert method is called exactly once

### Requirement: GenericEndpointHelper routes HTTP verbs to CRUD operations
`GenericEndpointHelper` SHALL dispatch GET, POST, PUT, and DELETE requests to the appropriate `GenericDbHelper` methods.

#### Scenario: GET request with ID calls find_by_id
- **WHEN** `handle_request(method="GET", item_id="xyz")` is called
- **THEN** the underlying `GenericDbHelper.find_by_id("xyz")` is called

#### Scenario: POST request calls create_item
- **WHEN** `handle_request(method="POST", body={...})` is called
- **THEN** `GenericDbHelper.create_item(...)` is called with the request body

#### Scenario: DELETE request calls delete_item
- **WHEN** `handle_request(method="DELETE", item_id="xyz")` is called
- **THEN** `GenericDbHelper.delete_item("xyz")` is called

#### Scenario: Unsupported method returns error result
- **WHEN** `handle_request(method="PATCH", ...)` is called and PATCH is not configured
- **THEN** the result has `error == True`

### Requirement: GenericDbHelperWithRequest attaches request context to DB operations
`GenericDbHelperWithRequest` SHALL carry the framework-agnostic `Request` object through to DB helpers and use it to extract authorization headers for ownership filtering.

#### Scenario: Owner filter is applied when user_id is in token
- **WHEN** the request carries a valid JWT with a `sub` claim
- **THEN** DB queries include a filter restricting results to the authenticated user's records

#### Scenario: Admin user sees all records without owner filter
- **WHEN** the request carries a token for a user in the `admin` group
- **THEN** no owner filter is applied to DB queries
