## ADDED Requirements

### Requirement: users model CRUD operations return standard result dicts
`models/users/users.py` SHALL expose functions (e.g., `get_user_by_email`, `create_user`, `update_user`) that return `{'error': bool, 'error_message': str|None, 'resultset': Any}`. All DB calls SHALL be mocked.

#### Scenario: get_user_by_email returns user when found
- **WHEN** the mocked DB returns a user document matching the given email
- **THEN** `error == False` and `resultset` contains the user document

#### Scenario: get_user_by_email returns error when not found
- **WHEN** the mocked DB returns no documents
- **THEN** `error == True` and `error_message` is non-empty

#### Scenario: create_user hashes the password before DB insert
- **WHEN** `create_user({"email": "x@x.com", "password": "secret"})` is called
- **THEN** the DB insert is called with a `password` field that does not equal `"secret"`

#### Scenario: create_user returns error on duplicate email
- **WHEN** the mocked DB signals a duplicate-key error
- **THEN** `error == True` and `error_message` references the duplicate

### Requirement: logs model records entries in the standard result shape
`models/logs/logs.py` SHALL provide a function to insert a log entry into the DB. The input SHALL be sanitized (newlines stripped) before insertion.

#### Scenario: Log entry is inserted without newlines
- **WHEN** a log message containing `\n` is passed to the log-insert function
- **THEN** the value stored in the DB call argument contains no `\n`

#### Scenario: DB failure returns error result
- **WHEN** the mocked DB raises an exception during insert
- **THEN** the result has `error == True`

### Requirement: menu_options model returns structured menu data
`models/menu_options/menu_options.py` SHALL return the full menu tree as `resultset` from the DB or JSON config source, filtered by the authenticated user's groups.

#### Scenario: Admin user receives full menu
- **WHEN** `get_menu_options(groups=["admin"])` is called with a mocked data source
- **THEN** `resultset` contains all menu entries

#### Scenario: Regular user receives filtered menu
- **WHEN** `get_menu_options(groups=["user"])` is called
- **THEN** `resultset` excludes entries restricted to `admin` group

### Requirement: billing_utilities computes billing values correctly
`models/billing/billing_utilities.py` SHALL provide pure calculation functions (e.g., plan lookup, usage calculation) that are testable without DB access.

#### Scenario: Plan lookup returns correct plan details
- **WHEN** `get_plan("free")` is called with mocked plan data
- **THEN** the result contains the expected plan attributes (limit, price, name)

#### Scenario: Unknown plan returns error result
- **WHEN** `get_plan("nonexistent")` is called
- **THEN** `error == True`

### Requirement: const_tables constants are accessible as expected types
`constants/const_tables.py` SHALL expose constant tables (lists or dicts) whose values are correct Python primitives (strings, ints) so that downstream logic can use them without type coercion.

#### Scenario: Constant table is a non-empty dict or list
- **WHEN** each exported constant is accessed
- **THEN** it is a `dict` or `list` and has at least one entry

#### Scenario: Constant values are strings or ints
- **WHEN** the values of each constant table are iterated
- **THEN** every value (or every dict value) is a `str` or `int`
