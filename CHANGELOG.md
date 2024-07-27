# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).



## Unreleased
---

### New

### Changes

### Fixes

### Breaks


## 0.1.8 (2024-07-27)
---

### New
Add: ".nvmrc" file to set the repo default node version.

### Fixes
Fix: audio processing issues in FastAPI Apps by configuring expose_headers=["*"] in fastapi.add_middleware() [GS-95].


## 0.1.7 (2024-07-18)
---

### New
Add password and API Keys to AWS Secrets (encrypted) [GS-41].
Add plain envvars to AWS Secrets (unencrypted) [GS-96].
Add GET_SECRETS_ENABLED envvars to enable/disable cloud provider secrets [GS-41].
Add GET_SECRETS_ENVVARS and GET_SECRETS_CRITICAL envvars to fine-grained disabling of cloud secrets manager for critical secrets and plain envvars [GS-41].
Add CLOUD_PROVIDER envvar to .env.example, to choose the secrets manager cloud provider [GS-41].
Add GCP and Azure secrets initial code [GS-41].
Add AWS_DEPLOYMENT_TYPE envvar to .env.example, to have multiple deploying options like lambda, ec2 or fargate [GS-96].

### Changes
Change: # APP_STAGE=dev commented in .env.example to allow its value dynamic assignment [GS-41].
Change: minor linting changes.

### Fixes
Fix: "Can only access Blueprint.current_app if it's registered to an app." error in Chalice generic endpoint builder when there are specfici DB function [GS-81]


## 0.1.6 (2024-06-07)
---

### New
Mask the S3 URL and avoid AWS over-billing attacks [GS-72].
Add file uploads support to FastAPI [FA-246].
Add STORAGE_URL_SEED and APP_HOST_NAME env. vars. [GS-72].
Add "cryptography" dependency [GS-72].
Save all general and user's parameters read from DB in a /tmp/params_[user_id].json file for each user to speed up all API [GS-79].
Add specific functions to GenericDbHelper [GS-81].
Add "temp_filename()" to centralice the temporary filename path generation [GS-72].
Add "download_s3_object()" to download the file from the bucket and return the local path, instead of its content [GS-72].
Add requirements.txt generation to Makefile on publish.
Add ".PHONY" entries for all labels in Makefile.

### Changes
Redirect README instructions to the GenericSuite Documentation [GS-73].
BlueprintOne abstraction [GS-79].
Split GenericDbHelper and create GenericDbHelperSuper.
"blueprint" as mandatory parameter to GenericDbHelper, AppContext and app_context_and_set_env(), to make posible the specific functions to GenericDbHelper [GS-81].
"Config.formatted_log_message" loads APP_DB_NAME with "os.environ.get()" to report errors even when this env. var. is not set.

### Fixes
Fix "TypeError: 'AuthTokenPayload' object is not subscriptable" error in "generic_db_helpers.get_current_user" by using "request.user.public_id" instead of "self.request.user['public_id']" [FA-122].
Fix the CORS header Access-Control-Allow-Origin missing in FastAPI in Firefox [GS-69].
Handles the \@ issue in environment variables values when runs by "sam local start-api" [GS-90].
Fix AWS save_file_from_url() returns "public_url" instead of "attachment_url".


## 0.1.5 (2024-04-20)
---

### Changes
Add: "mangum" to make FastAPI work on AWS Lambda [FA-246].
License changed to ISC in "pyproject.toml" [FA-244].


## 0.1.4 (2024-04-20)
---

### New
Add FastAPI framework abstraction specific "create_app", "generate_blueprints_from_json" and Auth Request elements [FA-246].
Add basic endpoints for menu_options and users (test, login, supad-create) for the FastAPI framework abstraction [FA-122].

### Changes
"view_func1" renamed as "view_function" in "endpoints.json" configuration file.
AWS_API_GATEWAY_STAGE env. var. removed.
AWS_LAMBDA_FUNCTION_ROLE env. var. replaced by AWS_LAMBDA_FUNCTION_ROLE_QA, AWS_LAMBDA_FUNCTION_ROLE_STAGINNG, AWS_LAMBDA_FUNCTION_ROLE_DEMO and AWS_LAMBDA_FUNCTION_ROLE_PROD.
Replace "users" specific CRUD endpoint handler with the JSON configured one.
Change: "get_curr_user_id" to use "request.user.public_id" instead of "request.user.get("public_id")" [FA-122].
Change: "jwt.py" to have a separate def "get_general_authorized_request" to abstract it functionality between frameworks [FA-122].
Change "jwt.py" to call "AuthorizedRequest()" passing the 1st parameter as named "event_dict=request.to_original_event()" [FA-122]. 
Change: README with main image from the official documentation site [FA-246].
Change: Homepage pointed to "https://genericsuite.carlosjramirez.com/Backend-Development/GenericSuite-Core/" [FA-257].

### Fixes
Fix: FastAPI Response and Request objects to make it work with the framework abstraction layer standards [FA-246].
Fix: "generic_endpoint_helpers.py" and "security.py" to upper() the request.method because FastAPI send it in lower case.
Fix: /options endpoint to avoid redirection.
Fix: add "user_id" to the generic endpoint generator GET request method, and add "json_body" to the DELETE method to be compatible with array CRUDs.

### Breaks
Remove "pas-enc" endpoint for security reasons.


## 0.1.3 (2024-04-09)
---

### Changes
Add links to https://www.carlosjramirez.com/genericsuite/ in the README.


## 0.1.2 (2024-04-01)
---

### New
Add stage "demo" to APP_DB_ENGINE, APP_DB_NAME, APP_DB_URI, APP_CORS_ORIGIN, and AWS_S3_CHATBOT_ATTACHMENTS_BUCKET [FA-213].

### Changes
".env-example" renamed to ".env.example".
GenericSuite AI configuration environment variables removed from README.
The GenericSuite backend development scripts added to README.
License changed to ISC [FA-244].


## 0.1.1 (2024-03-19)
---

### New
Add Makefile `build`, `publish` and `publish-test` options.

### Changes
README enhanced instructions.


## 0.1.0 (2024-03-14)
---

### New
Publish to Pypi


## 0.0.6 (2024-03-03)
---

### New
Separate BE Generic Suite to publish on PyPi [FA-84].
Initial commit as an independent repository.


## 0.0.5 (2023-07-30)
---

### New
Add `generate_blueprints_from_json` function to generate the blueprints from the `endpoints.json` file.


## 0.0.4 (2023-07-13)
---

### New
Generic backend classes: config_dbdef_helpers, generic_db_helpers, generic_endpoint_helpers [FA-77].


## 0.0.3 (2023-07-12)
---

### New
Database definitions are in JSON files from an external git repository [FA-87].


## 0.0.2 (2022-08-22)
---

### New
DynamoDb emulated a-la MongoDB way.


## 0.0.1 (2022-03-10)
---

### New
Start programming of the generic editor.
