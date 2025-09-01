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

publish-test: requirements build
	# Pypi Test publish
	poetry run python3 -m twine upload --repository testpypi dist/*

publish: requirements build
	# Production Pypi publish
	poetry run python3 -m twine upload dist/*
