"""
App main module (create_app) for FastAPI
"""
from typing import Any
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from genericsuite.util.app_logger import log_info

from genericsuite.config.config import Config

from genericsuite.fastapilib.util.generic_endpoint_builder import (
    generate_blueprints_from_json
)
from genericsuite.fastapilib.endpoints import (
    users,
    menu_options,
    storage_retrieval,
    api_documentation,
)
from genericsuite.config.config_from_db import set_init_custom_data

DEBUG = False


def create_app(app_name: str, settings: Config = None) -> Any:
    """
    Create the FastAPI App
    """

    if settings is None:
        settings = Config()

    fastapi_app = FastAPI(title=app_name)

    fastapi_app.debug = settings.DEBUG

    # Custom data, to be used to store a dict for
    # GenericDbHelper specific functions
    fastapi_app.custom_data = set_init_custom_data()

    # CORS configuration
    set_cors_config(fastapi_app=fastapi_app, settings=settings)

    # Register generic endpoints
    fastapi_app.include_router(
        menu_options.router, prefix=f'/{settings.API_VERSION}/menu_options')
    fastapi_app.include_router(
        users.router, prefix=f'/{settings.API_VERSION}/users')
    fastapi_app.include_router(
        storage_retrieval.router, prefix=f'/{settings.API_VERSION}/assets')
    fastapi_app.include_router(
        api_documentation.router, prefix=f'/{settings.API_VERSION}/openapis')

    # Register generic endpoints (from the "endpoints.json" file)
    generate_blueprints_from_json(fastapi_app, 'endpoints')

    # Anounce app boot
    log_info(f"{settings.APP_NAME.capitalize()} v" +
             settings.APP_VERSION +
             " | Accepting connections from: " +
             settings.CORS_ORIGIN)
    if DEBUG:
        log_info(settings.debug_vars())

    # Save OpenAPI and kill the app
    path_to_save_openapi = os.environ.get('PATH_TO_SAVE_OPENAPI')
    if path_to_save_openapi:
        log_info(f"PATH_TO_SAVE_OPENAPI: {path_to_save_openapi}")
        log_info(
            "Saving OpenAPI JSON to: "
            f"{path_to_save_openapi}/{app_name}_openapi.json"
        )
        api_documentation.save_openapi_json(
            fastapi_app,
            f"{path_to_save_openapi}/{app_name}_openapi.json"
        )
        log_info(
            "Saving OpenAPI YAML to: "
            f"{path_to_save_openapi}/{app_name}_openapi.yaml"
        )
        api_documentation.save_openapi_yaml(
            fastapi_app,
            f"{path_to_save_openapi}/{app_name}_openapi.yaml"
        )
        log_info("OpenAPI saved successfully")

    return fastapi_app


def set_cors_config(fastapi_app, settings):
    """
    Sets the CORS configuration for the API.
    """
    origins = [settings.CORS_ORIGIN]
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


def create_handler(app_object):
    """
    Returns the FastAPI App as a valid AWS Lambda Function handler
    """
    return Mangum(app_object, lifespan="off")
