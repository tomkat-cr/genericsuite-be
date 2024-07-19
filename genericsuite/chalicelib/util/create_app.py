"""
App main module (create_app) for Chalice
"""
from typing import Any
import importlib
import logging

from genericsuite.util.app_logger import log_info
# from genericsuite.util.app_logger import log_debug

from genericsuite.config.config import Config

from genericsuite.chalicelib.endpoints import users
from genericsuite.chalicelib.endpoints import menu_options
from genericsuite.chalicelib.endpoints import storage_retrieval
from genericsuite.chalicelib.util.generic_endpoint_builder import (
    generate_blueprints_from_json
)

from genericsuite.config.config_from_db import set_init_custom_data

# from chalice import Chalice
framework_class = importlib.import_module("chalice")

DEBUG = False


def create_app(app_name: str, settings=None) -> Any:
    """ Create the Chalice App """

    if settings is None:
        settings = Config()

    chalice_app = framework_class.Chalice(app_name=app_name)
    chalice_app.experimental_feature_flags.update(['BLUEPRINTS'])

    chalice_app.debug = settings.DEBUG

    # Custom data, to be used to store a dict for
    # GenericDbHelper specific functions
    chalice_app.custom_data = set_init_custom_data()

    # App wide log level
    if not settings.DEBUG:
        chalice_app.log.setLevel(logging.INFO)

    # CORS configuration
    chalice_app.api.cors = set_cors_config(
        cors_config_class=framework_class.CORSConfig,
        settings=settings)

    # Set Content-type: multipart/form-data as Binary
    # to properly handle image uploads
    chalice_app.api.binary_types.append("multipart/form-data")
    # log_debug(f'api.binary_types: {chalice_app.api.binary_types}')

    # Register general endpoints
    chalice_app.register_blueprint(menu_options.bp, url_prefix='/menu_options')
    # log_info("Registered menu_options blueprint")
    chalice_app.register_blueprint(users.bp, url_prefix='/users')
    # log_info("Registered users blueprint")
    chalice_app.register_blueprint(storage_retrieval.bp, url_prefix='/asset')
    # log_info("Registered storage_retrieval blueprint")

    # Register generic endpoints (from the "endpoints.json" file)
    generate_blueprints_from_json(chalice_app, 'endpoints')

    # Anounce app boot
    log_info(f"{settings.APP_NAME.capitalize()} v" +
             settings.APP_VERSION +
             " | Accepting connections from: " +
             settings.CORS_ORIGIN)
    if DEBUG:
        log_info(settings.debug_vars())

    return chalice_app


def set_cors_config(cors_config_class, settings):
    """
    Sets the CORS configuration for the API.
    Returns:
        CORSConfig: The CORS configuration.
    """
    cors_config = cors_config_class(
        allow_origin=settings.CORS_ORIGIN,
        allow_headers=[
            settings.HEADER_TOKEN_ENTRY_NAME,
            'Access-Control-Allow-Origin',
            'Content-Type',
            'Access-Control-Allow-Headers',
        ],
        max_age=600,
        expose_headers=[
            settings.HEADER_TOKEN_ENTRY_NAME,
            'Access-Control-Allow-Origin',
            'Content-Type',
            'Content-Disposition',
        ],
        allow_credentials=True
    )
    return cors_config
