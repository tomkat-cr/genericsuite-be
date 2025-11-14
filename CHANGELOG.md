# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).


## [Unreleased]

### Added

### Changed

### Fixed

### Removed

### Security


## [0.2.0] - 2025-11-14

### Added
- Implement MCP on GS BE Core [GS-189].
- Add PEM_TOOL envvar to select the Python package and dependency management tool (uv, pipenv, and poetry), default to "uv" [GS-77].
- Add AUTO_RELOAD envvar to .env.example, to fix some issues with the "--auto-reload" / "--reload" option running the app in "run_aws.sh", Turborepo and "uv", default to "1" [GS-77].
- Add get_non_empty_value function to handle envvars declared in docker-composer.yml with no value.
- Add "help" command to Makefile.
- Add "install" command to Makefile for easier dependency management.  

### Changed
- Change Node.js version in .nvmrc to 20.
- Update README for clarity and accuracy.
- Update CHANGELOG format to be more semantic, for consistency, clarity, and "Keep a Changelog" standard.
- Update author email in pyproject.toml and setup.py.
- Modify pyproject.toml for compatibility with Python 3.10 and above.
- Add .vscode and .idea to the .gitignore file.
- Use Poetry to run build and publish commands in Makefile.  
- Code clean-up and linting changes.
- Authenticate API Keys from Database [GS-240]
- get_non_empty_value() function simplified using a more idiomatic Python pattern.

### Fixed
- Update urllib3 dependency to version 2.5.0 to fix a "make publish" error.
- Add new development dependencies "build" and "twine" to fix a "make publish" error.
- Fix the "boto3" and "s3transfer" conflict by removing "s3transfer" and "botocore" dependencies in the pyproject.toml file, because they are already included in "boto3".
- Update error handling in set_tool_context() function to retrieve a more concise error message from app_context [GS-240].

### Security
- Update "urllib3" to "^2.5.0" to fix security vulnerabilities [GS-219]:
    * "Catastrophic backtracking in URL authority parser when passed URL containing many @ characters"
    * "`Cookie` HTTP header isn't stripped on cross-origin redirects"
    * "urllib3 redirects are not disabled when retries are disabled on PoolManager instantiation"
    * "urllib3's Proxy-Authorization request header isn't stripped during cross-origin redirects"
    * "urllib3's request body not stripped after redirect from 303 status changes request method to GET"
    * "Using default SSLContext for HTTPS requests in an HTTPS proxy doesn't verify certificate hostname for proxy connection"
    * "`Cookie` HTTP header isn't stripped on cross-origin redirects"
- Update "Werkzeug" to "^3.0.6" to fix security vulnerabilities [GS-219]:
    * "Werkzeug possible resource exhaustion when parsing file data in forms"
    * "Werkzeug safe_join not safe on Windows"
- Update "cryptography" to "^44.0.1" to fix security vulnerability [GS-219]:
    * "pyca/cryptography has a vulnerable OpenSSL included in cryptography wheels"
- Update "Requests" to "^2.32.4" to fix security vulnerabilities [GS-219]:
    * "Requests vulnerable to .netrc credentials leak via malicious URLs"
    * "Using default SSLContext for HTTPS requests in an HTTPS proxy doesn't verify certificate hostname for proxy connection"
    * "Vulnerable OpenSSL included in cryptography wheels"
- Update "fastmcp" to "^2.13.0" to fix security vulnerabilities [GS-219]:
    * "FastMCP Auth Integration Allows for Confused Deputy Account Takeover"
    * "Authlib is vulnerable to Denial of Service via Oversized JOSE Segments"
- Update "mcp" to ">=1.21.0" to fix security vulnerabilities [GS-219]:
    * "Starlette vulnerable to O(n^2) DoS via Range header merging in ``starlette.responses.FileResponse``"
- Update "dnspython" to ">=2.6.1" to fix security vulnerabilities [GS-219]:
    * "Potential DoS via the Tudoor mechanism in eventlet and dnspython"
- Read the user data from the database in "get_api_key_auth()" instead of the "/tmp/params_[user_id].json" because storing sensitive or configuration data in a world-writable directory like /tmp is a security risk [GS-240].
- Add USER_PARAMS_FILE_ENABLED envvar to enable/disable user's parameters file "/tmp/params_[user_id].json", default to "0" to avoid security risks when running in a production environment [GS-240].


## [0.1.11] - 2025-07-08

### Added
- Add SSL_CERT_GEN_METHOD, BASE_DEVELOPMENT_PATH and SAM_BUILD_CONTAINER documentation to the .env.example file.
- Add JWT expiration time configuration with the EXPIRATION_MINUTES envvar [GS-200].
- Add RUN_PROTOCOL documentation to the .env.example file [GS-137].

### Changed
- Refactor query-param parsing for FastAPI [GS-200].
- Refactor request abstraction for Flask [GS-15].
- Add 'Access-Control-Expose-Headers' to the Flask response headers [GS-15].

### Fixed
- Fix "AttributeError: 'Request' object has no attribute 'to_dict'" error in get_query_params() when Flask framework is used in generic_array_crud() [GS-15].
- Fix error reporting in modify_item_in_db() is not showing the "json_file" variable content [GS-196].
- Fix the filter issue in the CRUD editor using FastAPI [GS-200].
- Linting changes.


## [0.1.10] - 2025-02-19

### Added
- Implement API keys to GS BE Core [GS-159].
- Implement the "CAUJF" endpoint to build all user's parameters local JSON files [GS-159].
- Generic Endpoint Builder for Flask [GS-15].

### Changed
- FastAPI get_current_user() now gets the headers from the request object (required by the API keys implementation) [GS-159].
- GenericDbHelperSuper class assigns None default value to Request and Blueprint, and {} to query_params and request_body properties, so it can be used by save_all_users_params_files() or other functions that does not have those objects in a given time [GS-159].
- GenericDbHelperSuper class avoid call specific_func_name() when blueprint is None [GS-159].
- Overall code clean up and linting changes.

### Fixed
- Fix poetry 2.x "The option --no-update does not exist" error message [FA-84].
- Missing "context" and "event_dict" properties, "to_dict" and "to_original_event" events, were added to the FastAPI Request class.
- Fix "'License :: OSI Approved :: ISC License' is not a valid classifier" error running "python3 -m twine upload dist/*" [FA-84].


## [0.1.9] - 2024-10-07

### Added
- Add "/users/current_user_d" endpoint [GS-2].
- Add GS_LOCAL_ENVIR envvar to detect a local database running in a docker container [GS-102].

### Changed
- Make DynamoDb tables with prefix work with the GS DB Abstraction [GS-102].
- Add error handling to all GenericDbHelper methods [GS-102].
- DynamoDB abstraction "update_one()" method handles update_one, replace_one, $addToSet and $pull operations [GS-102].
- App logger shows LOCAL condition and database engine.
- Botocore upgraded to "^1.35.20" [GS-128].
- S3transfer upgraded to "^0.10.0" [GS-128].


## [0.1.8] - 2024-07-27

### Added
- Add: ".nvmrc" file to set the repo default node version.

### Changed
- Upgrade dependency versions (pymongo==4.7.2 -> pymongo==4.8.0)

### Fixed
- Fix: audio processing issues in FastAPI Apps by configuring expose_headers=["*"] in fastapi.add_middleware() [GS-95].


## [0.1.7] - 2024-07-18

### Added
- Add password and API Keys to AWS Secrets (encrypted) [GS-41].
- Add plain envvars to AWS Secrets (unencrypted) [GS-96].
- Add GET_SECRETS_ENABLED envvars to enable/disable cloud provider secrets [GS-41].
- Add GET_SECRETS_ENVVARS and GET_SECRETS_CRITICAL envvars to fine-grained disabling of cloud secrets manager for critical secrets and plain envvars [GS-41].
- Add CLOUD_PROVIDER envvar to .env.example, to choose the secrets manager cloud provider [GS-41].
- Add GCP and Azure secrets initial code [GS-41].
- Add AWS_DEPLOYMENT_TYPE envvar to .env.example, to have multiple deploying options like lambda, ec2 or fargate [GS-96].

### Changed
- Change: # APP_STAGE=dev commented in .env.example to allow its value dynamic assignment [GS-41].
- Change: minor linting changes.

### Fixed
- Fix: "Can only access Blueprint.current_app if it's registered to an app." error in Chalice generic endpoint builder when there are specfici DB function [GS-81]


## [0.1.6] - 2024-06-07

### Added
- Mask the S3 URL and avoid AWS over-billing attacks [GS-72].
- Add file uploads support to FastAPI [FA-246].
- Add STORAGE_URL_SEED and APP_HOST_NAME env. vars. [GS-72].
- Add "cryptography" dependency [GS-72].
- Save all general and user's parameters read from DB in a /tmp/params_[user_id].json file for each user to speed up all API [GS-79].
- Add specific functions to GenericDbHelper [GS-81].
- Add "temp_filename()" to centralice the temporary filename path generation [GS-72].
- Add "download_s3_object()" to download the file from the bucket and return the local path, instead of its content [GS-72].
- Add requirements.txt generation to Makefile on publish.
- Add ".PHONY" entries for all labels in Makefile.

### Changed
- Redirect README instructions to the GenericSuite Documentation [GS-73].
- BlueprintOne abstraction [GS-79].
- Split GenericDbHelper and create GenericDbHelperSuper.
- "blueprint" as mandatory parameter to GenericDbHelper, AppContext and app_context_and_set_env(), to make posible the specific functions to GenericDbHelper [GS-81].
- "Config.formatted_log_message" loads APP_DB_NAME with "os.environ.get()" to report errors even when this env. var. is not set.

### Fixed
- Fix "TypeError: 'AuthTokenPayload' object is not subscriptable" error in "generic_db_helpers.get_current_user" by using "request.user.public_id" instead of "self.request.user['public_id']" [FA-122].
- Fix the CORS header Access-Control-Allow-Origin missing in FastAPI in Firefox [GS-69].
- Handles the \@ issue in environment variables values when runs by "sam local start-api" [GS-90].
- Fix AWS save_file_from_url() returns "public_url" instead of "attachment_url".


## [0.1.5] - 2024-04-20

### Added
- Add: "mangum" to make FastAPI work on AWS Lambda [FA-246].
- License changed to ISC in "pyproject.toml" [FA-244].


## [0.1.4] - 2024-04-20

### Added
- Add FastAPI framework abstraction specific "create_app", "generate_blueprints_from_json" and Auth Request elements [FA-246].
- Add basic endpoints for menu_options and users (test, login, supad-create) for the FastAPI framework abstraction [FA-122].

### Changed
- "view_func1" renamed as "view_function" in "endpoints.json" configuration file.
- AWS_API_GATEWAY_STAGE env. var. removed.
- AWS_LAMBDA_FUNCTION_ROLE env. var. replaced by AWS_LAMBDA_FUNCTION_ROLE_QA, AWS_LAMBDA_FUNCTION_ROLE_STAGINNG, AWS_LAMBDA_FUNCTION_ROLE_DEMO and AWS_LAMBDA_FUNCTION_ROLE_PROD.
- Replace "users" specific CRUD endpoint handler with the JSON configured one.
- Change: "get_curr_user_id" to use "request.user.public_id" instead of "request.user.get("public_id")" [FA-122].
- Change: "jwt.py" to have a separate def "get_general_authorized_request" to abstract it functionality between frameworks [FA-122].
- Change "jwt.py" to call "AuthorizedRequest()" passing the 1st parameter as named "event_dict=request.to_original_event()" [FA-122]. 
- Change: README with main image from the official documentation site [FA-246].
- Change: Homepage pointed to "https://genericsuite.carlosjramirez.com/Backend-Development/GenericSuite-Core/" [FA-257].

### Fixed
- Fix: FastAPI Response and Request objects to make it work with the framework abstraction layer standards [FA-246].
- Fix: "generic_endpoint_helpers.py" and "security.py" to upper() the request.method because FastAPI send it in lower case.
- Fix: /options endpoint to avoid redirection.
- Fix: add "user_id" to the generic endpoint generator GET request method, and add "json_body" to the DELETE method to be compatible with array CRUDs.

### Removed
- Remove "pas-enc" endpoint for security reasons.


## [0.1.3] - 2024-04-09
---

### Changed
- Add links to https://www.carlosjramirez.com/genericsuite/ in the README.


## [0.1.2] - 2024-04-01

### Added
- Add stage "demo" to APP_DB_ENGINE, APP_DB_NAME, APP_DB_URI, APP_CORS_ORIGIN, and AWS_S3_CHATBOT_ATTACHMENTS_BUCKET [FA-213].

### Changed
- ".env-example" renamed to ".env.example".
- GenericSuite AI configuration environment variables removed from README.
- The GenericSuite backend development scripts added to README.
- License changed to ISC [FA-244].


## [0.1.1] - 2024-03-19

### Added
- Add Makefile `build`, `publish` and `publish-test` options.

### Changed
- README enhanced instructions.


## [0.1.0] - 2024-03-14

### Added
- Publish to Pypi.


## [0.0.6] - 2024-03-03

### Added
- Separate BE Generic Suite to publish on PyPi [FA-84].
- Initial commit as an independent repository.


## [0.0.5] - 2023-07-30

### Added
- Add `generate_blueprints_from_json` function to generate the blueprints from the `endpoints.json` file.


## [0.0.4] - 2023-07-13

### Added
- Generic backend classes: config_dbdef_helpers, generic_db_helpers, generic_endpoint_helpers [FA-77].


## [0.0.3] - 2023-07-12

### Added
- Database definitions are in JSON files from an external git repository [FA-87].


## [0.0.2] - 2022-08-22

### Added
- DynamoDb emulated a-la MongoDB way.


## [0.0.1] - 2022-03-10

### Added
- Start the generic editor development.
