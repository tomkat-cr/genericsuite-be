# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).



## Unreleased
---

### New

### Changes

### Fixes

### Breaks


## Unreleased
---

### New
Add FastAPI framework abstraction specific "create_app", "generate_blueprints_from_json" and Auth Request elements [FA-246].
Add basic endpoints for menu_options and users (test, login, supad-create) for the FastAPI framework abstraction [FA-122].

### Changes
"view_func1" renamed as "view_function" in "endpoints.json" configuration file.
Fix Response and Request objects in FastAPI framework abstraction layer [FA-246].
AWS_API_GATEWAY_STAGE env. var. removed.
AWS_LAMBDA_FUNCTION_ROLE env. var. replaced by AWS_LAMBDA_FUNCTION_ROLE_QA, AWS_LAMBDA_FUNCTION_ROLE_STAGINNG, AWS_LAMBDA_FUNCTION_ROLE_DEMO and AWS_LAMBDA_FUNCTION_ROLE_PROD.
Replace "users" specific CRUD endpoint handler with the JSON configured one.
Change "get_curr_user_id" to use "request.user.public_id" instead of "request.user.get("public_id")" [FA-122].
Change "jwt.py" to have a separate def "get_general_authorized_request" to abstract it functionality between frameworks [FA-122].
Change "jwt.py" to call "AuthorizedRequest()" passing the 1st parameter as named "event_dict=request.to_original_event()" [FA-122]. 
Change: README with main image from the official documentation site [FA-246].

### Fixes
Fix "generic_endpoint_helpers.py" and "security.py" to upper() the request.method because FastAPI send it in lower case.

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
Add Makefile with `build`, `publish` and `publish-test` options.

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
