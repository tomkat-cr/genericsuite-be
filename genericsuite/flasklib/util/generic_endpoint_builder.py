"""
generic_endpoint_builder: generate endpoint from a json file for Flask.
"""
from flask import Flask, request
# from flask import jsonify, Blueprint
from pprint import pprint

from genericsuite.util.config_dbdef_helpers import get_json_def
from genericsuite.util.generic_endpoint_helpers import GenericEndpointHelper
from genericsuite.util.app_logger import log_debug
from genericsuite.util.utilities import return_resultset_jsonified_or_exception
from genericsuite.config.config_from_db import app_context_and_set_env
from genericsuite.config.config import Config

from genericsuite.flasklib.framework_abstraction import Request
from genericsuite.flasklib.util.blueprint_one import BlueprintOne
from genericsuite.util.jwt import (
    AuthorizedRequest,
    get_general_authorized_request
)

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
        blueprint = BlueprintOne(
            f"{bp_name}_gbfj", __name__,
            url_prefix=url_prefix)

        if DEBUG:
            log_debug(
                'GENERATE_BLUEPRINTS_FROM_JSON |' +
                f' bp_name: {bp_name}' +
                f' url_prefix: {url_prefix}'
            )

        # Add routes to the blueprint
        for route in definition['routes']:
            route_endpoint = route['endpoint'] if route['endpoint'] != "/" \
                else ""
            route_methods = route['methods']
            route_handler_type = route['handler_type']
            other_params = {
                "name": bp_name,
                "app": app,
                "params": route['params'],
                "blueprint": blueprint,
                "authorization": route.get('authorization', True),
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
                route_endpoint,
                generic_route_handler,
                None,
                methods=route_methods,
                # Params passed to the endpoint in the kwargs
                defaults=other_params,
            )

        # Register the blueprint with the Flask app
        app.register_blueprint(blueprint)


def generic_route_handler(*args, **kwargs):
    """
    Handles generic route requests and delegates to the appropriate
    CRUD operation based on the request parameters.

    Args:
        other_params (dict): Additional parameters.

    Returns:
        Response: The response from the CRUD operation.
    """
    self_debug = DEBUG
    # self_debug = True

    other_params = dict(kwargs)
    blueprint = other_params.pop('blueprint')
    if self_debug:
        log_debug(
            "Flask / generic_route_handler" +
            f"\n | args: {args}" +
            f"\n | kwargs: {kwargs}"
            f"\n | other_params: {other_params}" +
            "\n | request:")
        pprint(request.__dict__)
        log_debug("blueprint:")
        pprint(blueprint.__dict__)

    # Verify authentication
    current_request = Request()
    current_request.set_properties()
    if other_params["authorization"]:
        # current_request = get_general_authorized_request(request)
        current_request = get_general_authorized_request(current_request)
        _ = self_debug and log_debug(
            "Flask / generic_route_handler"
            f"\n | Get_general_authorized_request response: {current_request}"
        )
        if not isinstance(current_request, AuthorizedRequest):
            _ = self_debug and log_debug(
                "Flask / generic_route_handler"
                "\n | Invalid token or other error\n"
            )
            return current_request
    else:
        # Set environment variables from the database configurations.
        _ = self_debug and log_debug(
            "Flask / generic_route_handler"
            "\n | set Request() and set_properties()"
            f"\n | current_request: {current_request}"
            f"\n | type of current_request: {type(current_request)}"
        )

    app_context = app_context_and_set_env(
        request=current_request,
        blueprint=blueprint
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
