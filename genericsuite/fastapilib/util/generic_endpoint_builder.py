"""
Generic Endpoint builder for FastAPI
"""
from typing import Optional, Union

from pprint import pprint

from fastapi import FastAPI, Query, Body, Depends
from fastapi import Request as FaRequest
from pydantic import BaseModel

# from genericsuite.util.framework_abs_layer import FrameworkClass as FastAPI
# from genericsuite.util.framework_abs_layer import Response
from genericsuite.fastapilib.framework_abstraction import Response
from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
from genericsuite.fastapilib.util.dependencies import (
    get_current_user,
    build_request,
)

from genericsuite.util.config_dbdef_helpers import get_json_def
from genericsuite.util.generic_endpoint_helpers import GenericEndpointHelper
from genericsuite.util.app_logger import log_debug
from genericsuite.util.utilities import return_resultset_jsonified_or_exception
from genericsuite.config.config_from_db import app_context_and_set_env

from genericsuite.config.config import Config

DEBUG = False

class Endpoint(BaseModel):
    """
    A model for endpoint definitions.
    """
    name: str
    route: str
    method: str
    response_model: Optional[str] = None


def generate_blueprints_from_json(
    app: FastAPI,
    json_file: str = "endpoints",
) -> None:
    """
    Generates routes from a JSON file and registers them with
    the FastAPI app.

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

        if DEBUG:
            log_debug(
                'GENERATE_BLUEPRINTS_FROM_JSON |' +
                f' bp_name: {bp_name}' +
                f' url_prefix: {url_prefix}'
            )

        # Add routes to the router
        for route in definition['routes']:
            other_params = {
                "name": bp_name
            }
            other_params["params"] = route['params']

            if route['handler_type'] == "GenericEndpointHelper":
                route_handler = generic_route_handler
            else:
                route_handler = route['view_function']

            if DEBUG:
                log_debug(
                    'GENERATE_BLUEPRINTS_FROM_JSON |' +
                    f" route_endpoint: {route['endpoint']}" +
                    f" route_methods: {route['methods']}" +
                    f" route_handler_type: {route['handler_type']}" +
                    f" route_handler: {route_handler}" +
                    f" other_params: {other_params}"
                )

            for method in route['methods']:
                endpoint = {
                    "name": bp_name,
                    "route": f"{url_prefix}/{route['endpoint']}"
                        if route['endpoint'] and route['endpoint'] != '/'
                        else url_prefix,
                    "method": method,
                    "response_model": route.get("response_model")
                }
                endpoint_obj = Endpoint(**endpoint)

                # Assuming the response model is a Pydantic model and already imported
                response_model = globals()[endpoint_obj.response_model] \
                    if "response_model" in route else None

                other_params["method"] = endpoint_obj.method.lower()
                if other_params["method"] == 'get':
                    app.get(endpoint_obj.route, response_model=response_model,
                            tags=[bp_name])(
                        create_endpoint_function(other_params)
                    )
                elif other_params["method"] == 'post':
                    app.post(endpoint_obj.route, response_model=response_model,
                             tags=[bp_name])(
                        create_endpoint_function(other_params)
                    )
                elif other_params["method"] == 'put':
                    app.put(endpoint_obj.route, response_model=response_model,
                            tags=[bp_name])(
                        create_endpoint_function(other_params)
                    )
                elif other_params["method"] == 'delete':
                    app.delete(endpoint_obj.route, response_model=response_model,
                               tags=[bp_name])(
                        create_endpoint_function(other_params)
                    )


def generic_route_handler(
    # *args,
    **kwargs,
) -> Response:
    """
    Handles generic route requests and delegates to the appropriate
    CRUD operation based on the request parameters.

    Args:
        kwargs (dict): Additional keyword arguments.

    Returns:
        Response: The response from the CRUD operation.
    """
    other_params = kwargs["other_params"]
    request = kwargs["request"]
    blueprint = kwargs["blueprint"]

    if DEBUG:
        log_debug(
            "generic_route_handler |" +
            f" | kwargs: {kwargs}"
        )
        pprint(request.to_dict())

    if DEBUG:
        log_debug(
            "generic_route_handler |" +
            f" other_params: {other_params}" +
            f" request: {request}"
        )

    # Set environment variables from the database configurations.
    app_context = app_context_and_set_env(request=request, blueprint=blueprint)
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


def create_endpoint_function(other_params: dict) -> callable:
    """
    Creates a function that can be used as a FastAPI endpoint.

    Args:
        other_params (dict): The other parameters to pass to the endpoint function.

    Returns:
        callable: The endpoint function.
    """
    router = BlueprintOne()

    async def generic_get(
        request: FaRequest,
        current_user: str = Depends(get_current_user),
        _id: str = Query(None, min_length=3, max_length=50, alias="id"),
        user_id: Union[str, None] = Query(None),
        limit: Union[int, None] = Query(None, ge=1, le=100000),
        page: Union[int, None] = Query(None, ge=1, le=100000),
        like_param: str = Query(None),
        comb_param: str = Query(None),
    ):
        """
        Handles generic GET requests, to get one row by id, a Like Search,
        get one row by additional_query_params, or fetch the
        paginated-limited-filtered list.

        Args:
            id (str): The ID of the record to retrieve.
            limit (int): The maximum number of records to retrieve.
            page (int): The page number to retrieve.
            like_param (str): The parameter to search for records.
            comb_param (str): The parameter to combine with the like_param.

        Returns:
            Response: The response from the GET operation.
        """
        gs_request = build_request(
            method="get",
            query_params={
                "id": _id,
                "limit": limit,
                "page": page,
                "like_param": like_param,
                "comb_param": comb_param,
                "user_id": user_id,
            },
            headers={
                "current_user": current_user,
            }
        )
        router.set_current_request(request, gs_request)
        return generic_route_handler(other_params=other_params,
            request=gs_request, blueprint=router)

    async def generic_post(
        request: FaRequest,
        current_user: str = Depends(get_current_user),
        json_body: dict = Body(...),
    ):
        """
        Handles generic POST requests, to create one item.

        Args:
            json_body (dict) = data for the item to be created

        Returns:
            Response: The response from the GET operation.
        """
        gs_request = build_request(
            method="post",
            json_body=json_body,
            headers={
                "current_user": current_user,
            },
        )
        router.set_current_request(request, gs_request)
        return generic_route_handler(other_params=other_params,
            request=gs_request, blueprint=router)

    async def generic_put(
        request: FaRequest,
        current_user: str = Depends(get_current_user),
        json_body: dict = Body(...),
        update_item: str = Query(None),
    ):
        """
        Handles generic PUT requests, to update one item.

        Args:
            json_body (dict) = data to be updated
            update_item (str): "1" apply update_one() instead
                    of replace_one(). Defaults to "0"

        Returns:
            Response: The response from the GET operation.
        """
        gs_request = build_request(
            method="put",
            query_params={
                "update_item": update_item,
            },
            json_body=json_body,
            headers={
                "current_user": current_user,
            },
        )
        router.set_current_request(request, gs_request)
        return generic_route_handler(other_params=other_params,
            request=gs_request, blueprint=router)

    async def generic_delete(
        request: FaRequest,
        current_user: str = Depends(get_current_user),
        _id: str = Query(None, min_length=3, max_length=50, alias="id"),
        json_body: Optional[Union[dict, None]] = Body(...),
    ):
        """
        Handles generic DELETE requests, to delete one row by id.

        Args:
            id (str): The ID of the record to retrieve.

        Returns:
            Response: The response from the GET operation.
        """
        gs_request = build_request(
            method="delete",
            query_params={
                "id": _id,
            },
            json_body=json_body,
            headers={
                "current_user": current_user,
            },
        )
        router.set_current_request(request, gs_request)
        return generic_route_handler(other_params=other_params,
            request=gs_request, blueprint=router)

    if other_params["method"] == 'post':
        return generic_post
    if other_params["method"] == 'put':
        return generic_put
    if other_params["method"] == 'delete':
        return generic_delete
    # Defaults to other_params["method"] == 'get'
    return generic_get
