"""
App main module (create_app) for Flask
"""
from typing import Any
import logging
import os

from flask import Flask
from flask_cors import CORS

from genericsuite.util.app_logger import log_info
from genericsuite.config.config import Config
from genericsuite.config.config_from_db import set_init_custom_data

from genericsuite.flasklib.endpoints import users
from genericsuite.flasklib.endpoints import menu_options
from genericsuite.flasklib.endpoints import storage_retrieval
from genericsuite.flasklib.util.generic_endpoint_builder import (
    generate_blueprints_from_json
)

DEBUG = False


def create_app(app_name: str, settings=None) -> Any:
    """ Create the Flask App """

    if settings is None:
        settings = Config()

    app = Flask(app_name)
    app.config['DEBUG'] = settings.DEBUG
    app.secret_key = os.environ["FLASK_SECRET_KEY"]

    if DEBUG:
        log_info({'|||>>> app.config': app.config})

    # Custom data, to be used to store a dict for
    # GenericDbHelper specific functions
    app.custom_data = set_init_custom_data()

    # App wide log level
    app.logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # CORS configuration
    CORS(app, resources={r"/*": set_cors_config(settings)})

    # Register general endpoints
    app.register_blueprint(menu_options.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(storage_retrieval.bp)

    # Register generic endpoints (from the "endpoints.json" file)
    generate_blueprints_from_json(app, 'endpoints')

    # Announce app boot
    log_info(f"{settings.APP_NAME.capitalize()} v" +
             settings.APP_VERSION +
             " | Accepting connections from: " +
             settings.CORS_ORIGIN)
    if DEBUG:
        log_info(settings.debug_vars())

    return app


def set_cors_config(settings):
    """
    Sets the CORS configuration for the API.
    Returns:
        dict: The CORS configuration.
    """
    return {
        "origins": settings.CORS_ORIGIN,
        "methods": ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH",
                    "DELETE"],
        "allow_headers": [
            settings.HEADER_TOKEN_ENTRY_NAME,
            'x-project-id',     # (required for API Keys)
            'Access-Control-Allow-Origin',
            'Content-Type',
            'Access-Control-Allow-Headers',
            'Access-Control-Expose-Headers',
        ],
        "expose_headers": [
            settings.HEADER_TOKEN_ENTRY_NAME,
            'Access-Control-Allow-Origin',
            'Content-Type',
            'Content-Disposition',
        ],
        "supports_credentials": True,
        "max_age": 600,
    }
