"""
generic_endpoint_builder: generate endpoint from a json file.
"""
from pprint import pprint

# from chalice import Chalice
from genericsuite.util.framework_abs_layer import FrameworkClass as Chalice

# from chalice.app import Response
# from genericsuite.util.blueprint_one import BlueprintOne
from genericsuite.util.framework_abs_layer import Response, BlueprintOne

from genericsuite.util.config_dbdef_helpers import get_json_def
from genericsuite.util.generic_endpoint_helpers import GenericEndpointHelper
from genericsuite.util.jwt import (
    AuthorizedRequest,
    request_authentication
)
from genericsuite.util.app_logger import log_debug
from genericsuite.util.utilities import return_resultset_jsonified_or_exception
from genericsuite.config.config_from_db import app_context_and_set_env

from genericsuite.config.config import Config

DEBUG = False


def generate_blueprints_from_json(
    app: Chalice,
    json_file: str = "endpoints",
) -> None:
    """
    Generates blueprints from a JSON file and registers them with
    the Chalice app.

    Args:
        app (Chalice): The Chalice app to register the blueprints with.
        json_file (str, optional): The JSON file containing blueprint
        definitions. Defaults to "endpoints".
    """
    settings = Config()
    cnf_db_base_path = settings.GIT_SUBMODULE_LOCAL_PATH
    definitions = get_json_def(json_file, f'{cnf_db_base_path}/backend', [])

    for definition in definitions:
        bp_name = definition['name']
        url_prefix = f"/{definition.get('url_prefix', bp_name)}"
        blueprint = BlueprintOne(bp_name)

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
                "app": app
            }
            other_params["params"] = route['params']
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

            blueprint.route(
                path=route_endpoint,
                authorizor=request_authentication(),
                methods=route_methods,
                other_params=other_params,
            )(generic_route_handler)

        # Register the blueprint with the Chalice app
        app.register_blueprint(
            blueprint=blueprint,
            url_prefix=url_prefix,
            name_prefix=bp_name
        )


def generic_route_handler(
    request: AuthorizedRequest,
    *args,
    **kwargs,
) -> Response:
    """
    Handles generic route requests and delegates to the appropriate
    CRUD operation based on the request parameters.

    Args:
        request (AuthorizedRequest): The authorized request object.
        kwargs (dict): Additional keyword arguments.

    Returns:
        Response: The response from the CRUD operation.
    """
    if DEBUG:
        log_debug(
            "generic_route_handler |" +
            f" | kwargs: {kwargs}" +
            f" event: {request}:"
        )
        pprint(request.to_dict())

    other_params = kwargs["other_params"]
    if DEBUG:
        log_debug(
            "generic_route_handler |" +
            f" other_params: {other_params}" +
            f" request: {request}"
        )

    # Set environment variables from the database configurations.
    bp = BlueprintOne(other_params.get('name'))
    bp.register(app=other_params['app'], options={})
    app_context = app_context_and_set_env(
        request=request,
        blueprint=bp
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
