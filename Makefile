# .DEFAULT_GOAL := local
.PHONY: tests lock update requirements build publish-test publish
SHELL := /bin/bash

help:
	cat Makefile

lock:
	poetry lock

update:
	poetry update

install:
	poetry install

requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

build:
	# Build 'dist' directory needed for the Pypi publish
	poetry lock
	rm -rf dist
	poetry run python3 -m build

test-general:
	APP_NAME=test_app APP_STAGE=test APP_HOST_NAME=localhost APP_SECRET_KEY=fake_secret_key APP_SUPERADMIN_EMAIL=fake_email GIT_SUBMODULE_LOCAL_PATH=fake_path CLOUD_PROVIDER=aws AWS_REGION=us-east-1 GET_SECRETS_ENABLED=0 APP_DB_URI=fake_db_uri APP_DB_ENGINE=MONGODB APP_DB_NAME=mongo STORAGE_URL_SEED=xyz poetry run pytest

test-cov-general:
	APP_NAME=test_app APP_STAGE=test APP_HOST_NAME=localhost APP_SECRET_KEY=fake_secret_key APP_SUPERADMIN_EMAIL=fake_email GIT_SUBMODULE_LOCAL_PATH=fake_path CLOUD_PROVIDER=aws AWS_REGION=us-east-1 GET_SECRETS_ENABLED=0 APP_DB_URI=fake_db_uri APP_DB_ENGINE=MONGODB APP_DB_NAME=mongo STORAGE_URL_SEED=xyz poetry run pytest --cov=genericsuite --cov-report=term-missing

test-cov-append:
	APP_NAME=test_app APP_STAGE=test APP_HOST_NAME=localhost APP_SECRET_KEY=fake_secret_key APP_SUPERADMIN_EMAIL=fake_email GIT_SUBMODULE_LOCAL_PATH=fake_path CLOUD_PROVIDER=aws AWS_REGION=us-east-1 GET_SECRETS_ENABLED=0 APP_DB_URI=fake_db_uri APP_DB_ENGINE=MONGODB APP_DB_NAME=mongo STORAGE_URL_SEED=xyz poetry run pytest --cov=genericsuite --cov-append --cov-report=

test:
	CURRENT_FRAMEWORK=fastapi $(MAKE) test-general
	CURRENT_FRAMEWORK=flask $(MAKE) test-general
	CURRENT_FRAMEWORK=chalice $(MAKE) test-general
	CURRENT_FRAMEWORK=mcp $(MAKE) test-general

test-cov:
	-rm -f .coverage .coverage.*
	CURRENT_FRAMEWORK=fastapi $(MAKE) test-cov-append
	CURRENT_FRAMEWORK=flask $(MAKE) test-cov-append
	CURRENT_FRAMEWORK=chalice $(MAKE) test-cov-append
	CURRENT_FRAMEWORK=mcp $(MAKE) test-cov-append
	poetry run coverage report --show-missing --fail-under=30

sast-test: requirements
	# bash node_modules/genericsuite-be-scripts/scripts/sast_test.sh
	snyk auth
	snyk code test --severity-threshold=high --all-projects .
	snyk test --severity-threshold=high --all-projects .

publish-test: sast-test build
	# Pypi Test publish
	poetry run python3 -m twine upload --repository testpypi dist/*

publish: requirements build
	# Production Pypi publish
	poetry run python3 -m twine upload dist/* ${ARGS:-}
