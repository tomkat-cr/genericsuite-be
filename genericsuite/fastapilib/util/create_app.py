"""
App main module (create_app) for FastAPI
"""
from typing import Any

# import importlib
# import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from genericsuite.util.app_logger import log_info
# from genericsuite.util.app_logger import log_debug

from genericsuite.config.config import Config

from genericsuite.fastapilib.util.generic_endpoint_builder import (
    generate_blueprints_from_json
)
from genericsuite.fastapilib.endpoints import (
    users,
    menu_options,
    storage_retrieval,
)
from genericsuite.config.config_from_db import set_init_custom_data

# framework_class = importlib.import_module("fastapi")
# handler_wrapper_class = importlib.import_module("mangum")

DEBUG = False


def create_app(app_name: str, settings: Config = None) -> Any:
    """
    Create the FastAPI App
    """

    if settings is None:
        settings = Config()

    # fastapi_app = framework_class.FastAPI(title=app_name)
    fastapi_app = FastAPI(title=app_name)

    fastapi_app.debug = settings.DEBUG

    # Custom data, to be used to store a dict for
    # GenericDbHelper specific functions
    fastapi_app.custom_data = set_init_custom_data()

    # App wide log level
    # if not settings.DEBUG:
    #     fastapi_app.log.setLevel(logging.INFO)

    # CORS configuration
    set_cors_config(fastapi_app=fastapi_app, settings=settings)

    # Set Content-type: multipart/form-data as Binary
    # to properly handle image uploads
    # fastapi_app.api.binary_types.append("multipart/form-data")
    # log_debug(f'1) fastapi_app.api.binary_types: ' +
    #     '{fastapi_app.api.binary_types}')

    # Register generic endpoints
    fastapi_app.include_router(menu_options.router, prefix='/menu_options')
    fastapi_app.include_router(users.router, prefix='/users')
    fastapi_app.include_router(storage_retrieval.router, prefix='/asset')

    # Register generic endpoints (from the "endpoints.json" file)
    generate_blueprints_from_json(fastapi_app, 'endpoints')

    # Anounce app boot
    log_info(f"{settings.APP_NAME.capitalize()} v" +
             settings.APP_VERSION +
             " | Accepting connections from: " +
             settings.CORS_ORIGIN)
    if DEBUG:
        log_info(settings.debug_vars())

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
    # return handler_wrapper_class.Mangum(app_object, lifespan="off")
    return Mangum(app_object, lifespan="off")
