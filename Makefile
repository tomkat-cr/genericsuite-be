# .DEFAULT_GOAL := local
.PHONY: tests lock update requirements build publish-test publish
SHELL := /bin/bash

lock:
	poetry lock

update:
	poetry update

requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

build:
	# Build 'dist' directory needed for the Pypi publish
	poetry lock --no-update
	rm -rf dist
	python3 -m build

publish-test: requirements build
	# Pypi Test publish
	python3 -m twine upload --repository testpypi dist/*

publish: requirements build
	# Production Pypi publish
	python3 -m twine upload dist/*
