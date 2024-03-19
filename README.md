# The GenericSuite for Python (backend version)

![GenericSuite Logo](https://github.com/tomkat-cr/genericsuite-fe/blob/main/src/lib/images/gs_logo_circle.png)

GenericSuite is a versatile backend solution, designed to provide a comprehensive suite of features for Python APIs. It supports various frameworks including Chalice, FastAPI, and Flask, making it adaptable to a range of projects. This repository contains the backend logic, utilities, and configurations necessary to build and deploy scalable and maintainable applications.

## Features

- **Framework Agnostic**: Supports Chalice, FastAPI, and Flask frameworks.
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

### AWS account and credentials

If you plan to deploy the App in the AWS Cloud:

* AWS account, see [free tier](https://aws.amazon.com/free).
* AWS Token, see [Access Keys](https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-east-1#/security_credentials?section=IAM_credentials).
* AWS Command-line interface, see [awscli](https://formulae.brew.sh/formula/awscli).
* API Framework and Serverless Deployment, see [Chalice](https://github.com/aws/chalice).

## Getting Started

To get started with GenericSuite, follow these steps:

### Initiate your project

To create the project directory for the App's backend API. E.g. `exampleapp_backend`, instrctions will depend on the dependency management of your preference:

```bash
```

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

To use GenericSuite in your project, install it with the following command(s):

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

## Usage

1. **Select Your Framework**: Depending on your project, choose between [Chalice](https://aws.github.io/chalice/quickstart.html), [FastAPI](https://fastapi.tiangolo.com/), or [Flask](https://flask.palletsprojects.com/).
2. **Select Your Database of choice**: Implement database operations using the provided abstracted functions for [MongoDB](https://www.mongodb.com/) and [DynamoDB](https://aws.amazon.com/pm/dynamodb/).
3. **Included Authentication**: Your endpoints will be secured with [JWT](https://jwt.io/libraries)-based authentication.
4. **Define Endpoints**: Utilize the dynamic endpoint creation feature by defining your endpoints in a JSON configuration file. Visit the [Generic Suite Configuration Guide](https://github.com/tomkat-cr/genericsuite-fe/tree/main/src/configs) for more information.
2. **Define Menu Options**: Utilize the dynamic menu creation feature by defining your muenu and option access security in a JSON configuration file. Visit the [Generic Suite Configuration Guide](https://github.com/tomkat-cr/genericsuite-fe/tree/main/src/configs) for guidance.
2. **Define Table structures**: Utilize the dynamic table creation feature by defining your CRUD editors in JSON configuration files. Visit the [Generic Suite Configuration Guide](https://github.com/tomkat-cr/genericsuite-fe/tree/main/src/configs) for sample code and files.

## Configuration

Configure your application by setting up the necessary environment variables. Refer to the [.env.example](https://github.com/tomkat-cr/genericsuite-be/blob/main/.env-example) file for the required variables.

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
5. Application secret ket (to be used in password encryption)
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
8. CORS origin
```
# DEV
APP_CORS_ORIGIN_DEV=*
APP_FRONTEND_AUDIENCE_DEV=
```
```
# QA
APP_CORS_ORIGIN_QA=*
APP_CORS_ORIGIN_QA_CLOUD=https://app-qa.exampleapp.com
APP_CORS_ORIGIN_QA_LOCAL=http://localhost:3000
APP_FRONTEND_AUDIENCE_QA=
```
```
# Staging
APP_CORS_ORIGIN_STAGING=*
APP_FRONTEND_AUDIENCE_STAGING=
```
```
# PROD
APP_CORS_ORIGIN_PROD=*
APP_FRONTEND_AUDIENCE_PROD=
```
9. Current framework options: chalice, flask, fastapi
```
CURRENT_FRAMEWORK=chalice
```
10. JSON configuration files location and git URL
```
GIT_SUBMODULE_LOCAL_PATH=lib/config_dbdef
GIT_SUBMODULE_URL=git://github.com/username/configs_repo_name.git
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
AWS_S3_BUCKET_NAME_FE=aws-s3-bucket-name
AWS_REGION=aws-region
AWS_API_GATEWAY_STAGE=aws-api-gateway-stage
AWS_LAMBDA_FUNCTION_NAME=aws-lambda-function-name
AWS_LAMBDA_FUNCTION_ROLE=aws-lambda-function-role
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
TEST_APP_URL=http://app.exampleapp.local:5002
```
19. Flask configuration
```
FLASK_APP=index.py
```
20. For GenricSuite AI only
```
# Aplicacion AI assistant name
AI_ASSISTANT_NAME=ExampleBot

# AWS configuration
AWS_S3_CHATBOT_ATTACHMENTS_BUCKET_DEV=aws-s3-bucket-name
AWS_S3_CHATBOT_ATTACHMENTS_BUCKET_QA=aws-s3-bucket-name
AWS_S3_CHATBOT_ATTACHMENTS_BUCKET_STAGING=aws-s3-bucket-name
AWS_S3_CHATBOT_ATTACHMENTS_BUCKET_PROD=aws-s3-bucket-name
```

## App structure

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
├── .env
├── .env-example
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── Makefile
├── Pipfile
├── Pipfile.lock
├── README.md
├── app.py
├── chalicelib
│   └── endpoints
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

## Code examples and JSON configuration files

The main menu, API endpoints and CRUD editor configurations are defined in the JSON configuration files.

You can find examples about configurations and how to code an App [here](https://github.com/tomkat-cr/genericsuite-fe/blob/main/src/configs/README.md) and the different JSON files in the [src/configs/frontend](https://github.com/tomkat-cr/genericsuite-fe/blob/main/src/configs/frontend) and [src/configs/backend](https://github.com/tomkat-cr/genericsuite-fe/blob/main/src/configs/backend) directories.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

This project is developed and maintained by Carlos J. Ramirez. For more information or to contribute to the project, visit [GenericSuite on GitHub](https://github.com/tomkat-cr/genericsuite-be).

Happy Coding!