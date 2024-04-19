# The GenericSuite for Python (backend version)

<img 
    align="right"
    width="100"
    height="100"
    src="https://genericsuite.carlosjramirez.com/images/gs_logo_circle.svg"
    title="GenericSuite logo by Carlos J. Ramirez"
/>

[GenericSuite](https://www.carlosjramirez.com/genericsuite) is a versatile backend solution, designed to provide a comprehensive suite of features for Python APIs. It supports various frameworks including FastAPI, Flask and Chalice, making it adaptable to a range of projects. This repository contains the backend logic, utilities, and configurations necessary to build and deploy scalable and maintainable applications.

## Features

- **Framework Agnostic**: Supports FastAPI, Flask, and Chalice frameworks.
- **Database Support**: Includes abstracted database operations for both MongoDB and DynamoDB, offering flexibility in choosing the database.
- **Authentication**: Implements JWT-based authentication, providing secure access to endpoints.
- **Dynamic Endpoint Creation**: Allows for defining endpoints dynamically through JSON configurations.
- **Utilities**: A collection of utilities for tasks such as sending emails, parsing multipart data, handling passwords, and more.
- **Billing Utilities**: Tools for managing billing plans and user subscriptions.
- **Menu Options**: Functionality to manage and retrieve authorized menu options based on user roles.

## Pre-requisites

- [Python](https://www.python.org/downloads/) >= 3.9 and < 4.0
- [Git](https://www.atlassian.com/git/tutorials/install-git)
- Make: [Mac](https://formulae.brew.sh/formula/make) | [Windows](https://stackoverflow.com/questions/32127524/how-to-install-and-use-make-in-windows)
- Node version 18+, installed via [NVM (Node Package Manager)](https://nodejs.org/en/download/package-manager) or [NPM and Node](https://nodejs.org/en/download) install.

### AWS account and credentials

If you plan to deploy the App in the AWS Cloud:

* AWS account, see [free tier](https://aws.amazon.com/free).
* AWS Token, see [Access Keys](https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-east-1#/security_credentials?section=IAM_credentials).
* AWS Command-line interface, see [awscli](https://formulae.brew.sh/formula/awscli).
* API Framework and Serverless Deployment, see [Chalice](https://github.com/aws/chalice).

## Getting Started

To get started with [GenericSuite](https://www.carlosjramirez.com/genericsuite), follow these steps:

### Initiate your project

To create the project directory for the App's backend API. E.g. `exampleapp_backend`, instrctions will depend on the dependency management of your preference:

```bash
# Pip
mkdir -p exampleapp_backend/exampleapp_backend
cd exampleapp_backend
python3 -m venv venv
source venv/bin/activate
```

```bash
# Pipenv
# https://docs.pipenv.org/basics/
mkdir -p exampleapp_backend/exampleapp_backend
cd exampleapp_backend
pipenv install
```

```bash
# Poetry
# https://python-poetry.org/docs/basic-usage/
poetry start exampleapp_backend
cd exampleapp_backend
```

## Installation

To use [GenericSuite](https://www.carlosjramirez.com/genericsuite) in your project, install it with the following command(s):

### From Pypi

#### Pip
```bash
pip install genericsuite
```

#### Pipenv
```bash
pipenv install genericsuite
```

#### Poetry
```bash
poetry add genericsuite
```

### From a specific branch in the repository, e.g. "branch_x"

#### Pip
```bash
pip install git+https://github.com/tomkat-cr/genericsuite-be@branch_x
```

#### Pipenv
```bash
pipenv install git+https://github.com/tomkat-cr/genericsuite-be@branch_x
```

#### Poetry
```bash
poetry add git+https://github.com/tomkat-cr/genericsuite-be@branch_x
```

### Test dependencies

To execute the unit and integration test, install `pytest` and `coverage`:

#### Pip
```bash
pip install pytest coverage
```

#### Pipenv
```bash
pipenv install --dev pytest coverage
```

#### Poetry
```bash
poetry add --dev pytest coverage
```

### Development scripts installation

[The GenericSuite backend development scripts](https://github.com/tomkat-cr/genericsuite-be-scripts?tab=readme-ov-file#the-genericsuite-scripts-backend-version) contains utilities to build and deploy APIs made by The GenericSuite.

```bash
npm install -D genericsuite-be-scripts
```

## Features

1. **Select Your Framework**: Depending on your project, choose between [Chalice](https://aws.github.io/chalice/quickstart.html), [FastAPI](https://fastapi.tiangolo.com/), or [Flask](https://flask.palletsprojects.com/).
2. **Select Your Database of choice**: Implement database operations using the provided abstracted functions for [MongoDB](https://www.mongodb.com/) and [DynamoDB](https://aws.amazon.com/pm/dynamodb/).
3. **Included Authentication**: Your endpoints will be secured with [JWT](https://jwt.io/libraries)-based authentication.
4. **Define Endpoints**: Utilize the dynamic endpoint creation feature by defining your endpoints in a JSON configuration file. Visit the [Generic Suite Configuration Guide](https://github.com/tomkat-cr/genericsuite-fe/tree/main/src/configs) for more information.
2. **Define Menu Options**: Utilize the dynamic menu creation feature by defining your muenu and option access security in a JSON configuration file. Visit the [Generic Suite Configuration Guide](https://github.com/tomkat-cr/genericsuite-fe/tree/main/src/configs) for guidance.
2. **Define Table structures**: Utilize the dynamic table creation feature by defining your CRUD editors in JSON configuration files. Visit the [Generic Suite Configuration Guide](https://github.com/tomkat-cr/genericsuite-fe/tree/main/src/configs) for sample code and files.

## Configuration

Configure your application by setting up the necessary environment variables. Refer to the [.env.example](https://github.com/tomkat-cr/genericsuite-be/blob/main/.env.example) and [config.py](https://github.com/tomkat-cr/genericsuite-be/blob/main/genericsuite/config/config.py) files for the available options.

1. Aplicacion name
```
APP_NAME=ExampleApp
```
2. Aplicacion domain
```
APP_DOMAIN_NAME=exampleapp.com
```
3. Application default language
```
DEFAULT_LANG=en
```
4. Stage and Debug flag
```
# DEV
# Application debug (0,1)
APP_DEBUG=1
# Application environment: dev, qa, staging, prod
APP_STAGE=dev
```
```
# QA
APP_DEBUG=1
APP_STAGE=qa
```
```
# PROD
APP_DEBUG=0
APP_STAGE=prod
```
5. Application secret key (to be used in password encryption)
```
APP_SECRET_KEY=xxxx
```
6. Application super administrator email
```
APP_SUPERADMIN_EMAIL=xxxx
```
7. Database configuration
- For AWS DynamoDB
```
# DEV: docker
APP_DB_ENGINE_DEV=DYNAMO_DB
APP_DB_NAME_DEV=
APP_DB_URI_DEV=http://localhost:8000
```
```
# QA: AWS DynamoDB
APP_DB_ENGINE_QA=DYNAMO_DB
APP_DB_NAME_QA=
APP_DB_URI_QA=
```
```
# PROD: AWS DynamoDB
APP_DB_ENGINE_PROD=DYNAMO_DB
APP_DB_NAME_PROD=
APP_DB_URI_PROD=
```
```
# # DEMO: AWS DynamoDB
# APP_DB_ENGINE_DEMO=DYNAMO_DB
# APP_DB_NAME_DEMO=
# APP_DB_URI_DEMO=
```
- For MongoDB
```
# DEV: Docker container
APP_DB_ENGINE_DEV=MONGO_DB
APP_DB_NAME_DEV=mongo
APP_DB_URI_DEV=mongodb://root:example@app.exampleapp.local:27017/
```
```
# QA: MongoDB Atlas
APP_DB_ENGINE_QA=MONGO_DB
APP_DB_NAME_QA=xxxx
APP_DB_URI_QA=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
```
```
# Staging: MongoDB Atlas
APP_DB_ENGINE_STAGING=MONGO_DB
APP_DB_NAME_STAGING=xxxx
APP_DB_URI_STAGING=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
```
```
# PROD: MongoDB Atlas
APP_DB_ENGINE_PROD=MONGO_DB
APP_DB_NAME_PROD=xxxx
APP_DB_URI_PROD=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
```
```
# DEMO: MongoDB Atlas
APP_DB_ENGINE_DEMO=MONGO_DB
APP_DB_NAME_DEMO=xxxx
APP_DB_URI_DEMO=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
```
8. CORS origin
```
# DEV
APP_CORS_ORIGIN_DEV=*
```
```
# QA
APP_CORS_ORIGIN_QA=*
APP_CORS_ORIGIN_QA_CLOUD=https://app-qa.exampleapp.com
APP_CORS_ORIGIN_QA_LOCAL=http://localhost:3000
```
```
# Staging
APP_CORS_ORIGIN_STAGING=https://app-qa.exampleapp.com
```
```
# PROD
APP_CORS_ORIGIN_PROD=https://app.exampleapp.com
```
```
# DEMO
APP_CORS_ORIGIN_DEMO=https://app-demo.exampleapp.com
```
9. Current framework options: chalice, flask, fastapi
```
CURRENT_FRAMEWORK=chalice
```
10. JSON configuration files location and git URL
```
GIT_SUBMODULE_LOCAL_PATH=lib/config_dbdef
GIT_SUBMODULE_URL=git://github.com/username/exampleapp_configs.git
```
11. Frontend application path (to copy version file during big lambdas deployment)
```
FRONTEND_PATH=../exampleapp_frontend
```
12. Local python version
```
PYTHON_VERSION=3.11.5
# PYTHON_VERSION=3.10.12
# PYTHON_VERSION=3.9.17
```
13. AWS Configuration
```
AWS_S3_BUCKET_NAME_FE=exampleapp-frontend-website-[STAGE]
AWS_REGION=aws-region
AWS_LAMBDA_FUNCTION_NAME=exampleapp-backend
AWS_LAMBDA_FUNCTION_ROLE_QA=exampleapp-api_handler-role-qa
AWS_LAMBDA_FUNCTION_ROLE_STAGING=exampleapp-api_handler-role-staging
AWS_LAMBDA_FUNCTION_ROLE_DEMO=exampleapp-api_handler-role-demo
AWS_LAMBDA_FUNCTION_ROLE_PROD=exampleapp-api_handler-role-prod
AWS_SSL_CERTIFICATE_ARN=arn:aws:acm:AWS-REGION:AWS-ACCOUNT:certificate/AWS-CERTIFICATE-UUID
```
15. SMTP Mail configuration
```
SMTP_SERVER=smtp_server
SMTP_PORT=smtp_port
SMTP_USER=smtp_user
SMTP_PASSWORD=smtp_password
SMTP_DEFAULT_SENDER=sender_email
```
16. Docker configuration
```
DOCKER_ACCOUNT=docker_account_username
```
17. Local development environment run configuration
```
# Options are: uvicorn, gunicorn, chalice, chalice_docker
# Chalice case: "chalice" to use http (running without docker) or "chalice_docker" to use https (with docker)
# http:
# RUN_METHOD="chalice"
# https:
RUN_METHOD="chalice_docker"
```
18. Tests configuration
```
# Testing enndpoint
TEST_APP_URL=http://app.exampleapp.local:5001
```
19. Run methods and framework App directory and entry point
```
#
# Default App main code directory
# for Chalice:
# https://aws.github.io/chalice/topics/packaging.html
# APP_DIR='.'
# for FastAPI:
# https://fastapi.tiangolo.com/tutorial/bigger-applications/?h=directory+structure#an-example-file-structure
# APP_DIR='app'
# for Flask:
# https://flask.palletsprojects.com/en/2.3.x/tutorial/layout/
# APP_DIR='flaskr'
#
# Default App entry point code file
# for Chalice:
# https://aws.github.io/chalice/topics/packaging.html
# APP_MAIN_FILE='app'
# for FastAPI:
# https://fastapi.tiangolo.com/tutorial/bigger-applications/?h=directory+structure#an-example-file-structure
# APP_MAIN_FILE='main'
# for Flask:
# https://flask.palletsprojects.com/en/2.3.x/tutorial/factory/
# APP_MAIN_FILE='__init__'
#
```
20. Flask configuration
```
FLASK_APP=__init__.py
```

## Framework installation

* [FastAPI installation](https://fastapi.tiangolo.com/#installation)
* [Flask installation](https://flask.palletsprojects.com/en/2.3.x/installation/)
* [Chalice installation](https://aws.github.io/chalice/quickstart.html)

## App structure

Suggested directory structure by framework:

* [FastAPI directory structure](https://fastapi.tiangolo.com/tutorial/bigger-applications/?h=directory+structure#an-example-file-structure)
* [Flask directory structure](https://flask.palletsprojects.com/en/2.3.x/tutorial/layout/)
* [Chalice directory structure](https://aws.github.io/chalice/topics/packaging.html)

This is a suggested App development repository structure for a FastAPI project:

```
.
├── app
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py
│   └── routers
│   │   ├── __init__.py
│   │   ├── items.py
│   │   └── users.py
│   └── internal
│       ├── __init__.py
│       └── admin.py
├── logs
│   └── .gitignore
├── .env
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── Makefile
├── Pipfile
├── Pipfile.lock
├── README.md
├── package-lock.json
├── package.json
├── requirements.txt
├── tests
│   ├── .env.for_test
│   ├── __init__.py
│   ├── assets
│   ├── conftest.py
│   └── pytest.ini
└── version.txt
```

This is a suggested App development repository structure for a Flask project:

```
.
├── flaskr/
│   ├── __init__.py
│   ├── items.py
│   ├── users.py
│   ├── admin.py
│   └── index.py
├── logs
│   └── .gitignore
├── package-lock.json
├── package.json
├── requirements.txt
├── tests
│   ├── .env.for_test
│   ├── __init__.py
│   ├── assets
│   ├── conftest.py
│   └── pytest.ini
├── .env
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── Makefile
├── Pipfile
├── Pipfile.lock
├── README.md
└── version.txt
```

This is a suggested App development repository structure for a Chalice project:

```
.
├── .chalice
│   ├── config-example.json
│   ├── config.json
│   ├── deployed
│   │   ├── dev.json
│   │   ├── qa.json
│   │   └── prod.json
│   ├── deployment
│   │   ├── deployment.zip
│   │   └── sam.json
│   ├── deployments
│   ├── dynamodb_cf_template.yaml
│   └── policy-qa.json
├── chalicelib
│   └── endpoints
│       ├── items.py
│       ├── users.py
│       ├── admin.py
│       └── __init__.py
├── lib
│   ├── .gitignore
│   ├── config
│   │   ├── __init__.py
│   │   └── config.py
│   ├── config_dbdef
│   │   ├── .gitignore
│   │   ├── CHANGELOG.md
│   │   ├── README.md
│   │   ├── backend
│   │   └── frontend
│   └── models
│       ├── __init__.py
│       ├── ai_chatbot
│       │   ├── __init__.py
│       │   └── ai_gpt_fn_index.py
│       ├── external_apis
│       │   └── __init__.py
│       └── utilities
├── logs
│   └── .gitignore
├── tests
│   ├── .env.for_test
│   ├── __init__.py
│   ├── assets
│   ├── conftest.py
│   └── pytest.ini
├── .env
├── .env.example
├── .gitignore
├── app.py
├── CHANGELOG.md
├── LICENSE
├── Makefile
├── package-lock.json
├── package.json
├── Pipfile
├── Pipfile.lock
├── README.md
├── requirements.txt
└── version.txt

```

## Code examples and JSON configuration files

The main menu, API endpoints and CRUD editor configurations are defined in the JSON configuration files.

You can find examples about configurations and how to code an App in the [GenericSuite App Creation and Configuration guide](https://github.com/tomkat-cr/genericsuite-fe/blob/main/src/configs/README.md).

## Usage

Check the [The GenericSuite backend development scripts](https://github.com/tomkat-cr/genericsuite-be-scripts?tab=readme-ov-file#the-genericsuite-scripts-backend-version) for more details.

## License

This project is licensed under the ISC License - see the [LICENSE](https://github.com/tomkat-cr/genericsuite-be/blob/main/LICENSE) file for details.

## Credits

This project is developed and maintained by Carlos J. Ramirez. For more information or to contribute to the project, visit [GenericSuite on GitHub](https://github.com/tomkat-cr/genericsuite-be).

Happy Coding!
