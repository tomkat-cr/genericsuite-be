## ADDED Requirements

### Requirement: framework_abs_layer normalizes requests to common Request object
`framework_abs_layer.py` SHALL provide functions that convert framework-specific request objects into a common internal `Request` representation, including headers, body, path params, and query params.

#### Scenario: FastAPI request is normalized
- **WHEN** a mock FastAPI `Request` object with headers and JSON body is passed to the normalization function
- **THEN** the resulting common `Request` has `headers`, `body`, and `method` populated correctly

#### Scenario: Flask request is normalized
- **WHEN** a mock Flask `Request` object is passed to the normalization function
- **THEN** the resulting common `Request` has equivalent attributes

#### Scenario: Authorization header is extracted
- **WHEN** the framework request has `Authorization: Bearer <token>` in headers
- **THEN** the common `Request.headers["Authorization"]` contains the full `Bearer <token>` value

### Requirement: FastAPI framework_abstraction returns correct HTTP responses
`fastapilib/framework_abstraction.py` SHALL convert common result dicts to FastAPI `JSONResponse` objects with the appropriate HTTP status codes.

#### Scenario: Success result maps to HTTP 200
- **WHEN** a result dict with `error == False` is passed to the FastAPI response builder
- **THEN** the resulting `JSONResponse` has `status_code == 200`

#### Scenario: Error result maps to HTTP 400 or 401
- **WHEN** a result dict with `error == True` and an auth-related message is passed
- **THEN** the resulting `JSONResponse` has `status_code` in [400, 401]

### Requirement: Flask framework_abstraction returns correct HTTP responses
`flasklib/framework_abstraction.py` SHALL convert common result dicts to Flask `Response` objects with JSON content-type and correct status codes.

#### Scenario: Success result maps to HTTP 200
- **WHEN** a result dict with `error == False` is converted
- **THEN** the Flask `Response` status code is 200 and content-type is `application/json`

#### Scenario: Error result includes error_message in body
- **WHEN** a result dict with `error == True` and a non-empty `error_message` is converted
- **THEN** the response body JSON contains the `error_message` value

### Requirement: Chalice framework_abstraction is tested with mocked Chalice Response
`chalicelib/framework_abstraction.py` SHALL be testable by mocking `chalice.Response`. All logic that calls `chalice.Response(...)` SHALL be exercisable without a real Chalice app context.

#### Scenario: Success result maps to Chalice Response with status 200
- **WHEN** the Chalice adapter converts a success result dict
- **THEN** the returned Chalice `Response` has `status_code == 200`

### Requirement: MCP framework_abstraction converts requests and results without framework side effects
`mcplib/framework_abstraction.py` SHALL normalize MCP tool call arguments into the common `Request` format and convert result dicts into MCP-compliant response structures.

#### Scenario: MCP arguments are mapped to Request fields
- **WHEN** a dict of MCP tool arguments is passed to the MCP adapter
- **THEN** the common `Request` has `body` equal to those arguments

#### Scenario: Result dict is converted to MCP response
- **WHEN** a success result dict is converted by the MCP adapter
- **THEN** the MCP response structure matches the expected schema (text content block or equivalent)
