"""
generic_endpoint_builder: generate endpoint from a json file for Flask.
"""
from flask import Flask, Blueprint, request
# from flask import jsonify
from functools import wraps
from pprint import pprint

from genericsuite.util.config_dbdef_helpers import get_json_def
from genericsuite.util.generic_endpoint_helpers import GenericEndpointHelper
from genericsuite.util.app_logger import log_debug
from genericsuite.util.utilities import return_resultset_jsonified_or_exception
from genericsuite.config.config_from_db import app_context_and_set_env
from genericsuite.config.config import Config

from genericsuite.flasklib.util.jwt import token_required
from genericsuite.flasklib.framework_abstraction import Request

DEBUG = False


def generate_blueprints_from_json(
    app: Flask,
    json_file: str = "endpoints",
) -> None:
    """
    Generates blueprints from a JSON file and registers them with
    the Flask app.

    Args:
        app (Flask): The Flask app to register the blueprints with.
        json_file (str, optional): The JSON file containing blueprint
        definitions. Defaults to "endpoints".
    """
    settings = Config()
    cnf_db_base_path = settings.GIT_SUBMODULE_LOCAL_PATH
    definitions = get_json_def(json_file, f'{cnf_db_base_path}/backend', [])

    for definition in definitions:
        bp_name = definition['name']
        url_prefix = f"/{definition.get('url_prefix', bp_name)}"
        blueprint = Blueprint(f"{bp_name}_gbfj", __name__,
                              url_prefix=url_prefix)

        if DEBUG:
            log_debug(
                'GENERATE_BLUEPRINTS_FROM_JSON |' +
                f' bp_name: {bp_name}' +
                f' url_prefix: {url_prefix}'
            )

        # Add routes to the blueprint
        for route in definition['routes']:
            route_endpoint = route['endpoint']
            route_methods = route['methods']
            route_handler_type = route['handler_type']
            other_params = {
                "name": bp_name,
                "app": app,
                "params": route['params']
            }

            if route_handler_type == "GenericEndpointHelper":
                route_handler = generic_route_handler
            else:
                route_handler = route['view_function']

            if DEBUG:
                log_debug(
                    'GENERATE_BLUEPRINTS_FROM_JSON |' +
                    f' route_endpoint: {route_endpoint}' +
                    f' route_methods: {route_methods}' +
                    f' route_handler_type: {route_handler_type}' +
                    f' route_handler: {route_handler}' +
                    f' other_params: {other_params}'
                )

            blueprint.add_url_rule(
                route_endpoint,
                endpoint=f"{bp_name}_{route_endpoint}",
                view_func=create_endpoint_function(other_params),
                methods=route_methods
            )

        # Register the blueprint with the Flask app
        app.register_blueprint(blueprint)


def create_endpoint_function(other_params: dict) -> callable:
    """
    Creates a function that can be used as a Flask endpoint.

    Args:
        other_params (dict): The other parameters to pass to the
            endpoint function.

    Returns:
        callable: The endpoint function.
    """
    @wraps(generic_route_handler)
    # @request_authentication()
    @token_required
    def wrapper(*args, **kwargs):
        return generic_route_handler(other_params=other_params)

    return wrapper


def generic_route_handler(other_params: dict):
    """
    Handles generic route requests and delegates to the appropriate
    CRUD operation based on the request parameters.

    Args:
        other_params (dict): Additional parameters.

    Returns:
        Response: The response from the CRUD operation.
    """
    if DEBUG:
        log_debug(
            "generic_route_handler |" +
            f" | other_params: {other_params}" +
            f" request: {request}"
        )
        pprint(request.__dict__)

    # Set environment variables from the database configurations.
    current_request = Request()
    current_request.set_properties()
    app_context = app_context_and_set_env(
        request=current_request,
        blueprint=other_params['name']
    )
    if app_context.has_error():
        return return_resultset_jsonified_or_exception(
            app_context.get_error_resultset()
        )

    ep_helper = GenericEndpointHelper(
        app_context=app_context,
        json_file=other_params['params']["json_file"],
        url_prefix=other_params["name"]
    )
    if ep_helper.dbo.table_type == "child_listing" \
       and ep_helper.dbo.sub_type == "array":
        return ep_helper.generic_array_crud()
    return ep_helper.generic_crud_main()


def get_query_param(param_name, default=None):
    """
    Helper function to get query parameters
    """
    return request.args.get(param_name, default)


def get_json_body():
    """
    Helper function to get JSON body
    """
    return request.get_json()
