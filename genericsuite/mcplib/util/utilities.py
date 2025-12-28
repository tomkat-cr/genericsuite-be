from typing import Optional, Dict, Any, Union
import json
import os

import jwt
from mcp.server.auth.middleware.auth_context \
    import get_access_token as get_access_token_mcp

from genericsuite.models.users.users import (
    login_user as login_user_model,
)
from genericsuite.config.config_from_db import app_context_and_set_env
from genericsuite.util.app_logger import log_debug
from genericsuite.util.jwt import (
    get_authorized_request,
    get_api_key_auth,
    token_encode,
    AuthTokenPayload,
)
from genericsuite.util.utilities import (
    get_default_resultset,
    get_id_as_string,
)
from genericsuite.util.generic_db_helpers import GenericDbHelper
from genericsuite.mcplib.framework_abstraction import (
    Request,
    Response,
    Blueprint,
)
from genericsuite.mcplib.util.McpServerApp import McpServerApp


DEBUG: bool = False
DEFAULT_JSON_INDENT = 2

MCP_MANDATORY_USER_ID = os.getenv("MCP_MANDATORY_USER_ID", "0") == "1"


def get_app_request(
    path: str,
    method: str = "GET",
    body: Optional[dict] = None,
    headers: Optional[dict] = None,
    other_params: Optional[dict] = None,
) -> Request:
    """
    Get the app request
    """
    request_params = {
        "method": method,
        "path": path,
    }
    if body is not None:
        request_params["body"] = body
    if headers is not None:
        request_params["headers"] = headers
    if other_params is not None:
        request_params["other_params"] = other_params
    return Request(**request_params)


def get_request_blueprint(
    name: str,
    app: McpServerApp,
    request: Request,
) -> Blueprint:
    """
    Get the request blueprint
    """
    return Blueprint(name, app, request)


def mcp_login_user(
    app: McpServerApp,
    username: str,
    password: str,
    other_params: Optional[dict] = None,
) -> Response:
    """
    User login via MCP
    """
    if other_params is None:
        other_params = {}
    other_params['username'] = username
    other_params['password'] = password
    request = get_app_request(
        path="user/login",
        method="POST",
    )
    blueprint = get_request_blueprint("login", app, request)
    return login_user_model(
        request=request,
        blueprint=blueprint,
        other_params=other_params)


def mcp_authenticate(
    app: McpServerApp,
    cac_object_list: list,
    username: str,
    password: str,
) -> str:
    """
    Authenticate user
    """
    request = get_app_request(
        path="user/login",
        method="POST",
    )
    login_result: Response = mcp_login_user(app, username, password)
    if login_result.status_code != 200:
        result = {
            "error": True,
            "message": login_result.body,
            "login_result": login_result.to_dict(),
        }
        return resource_result(result)
    set_tool_context(
        request=request,
        resultset=json.loads(login_result.body).get("resultset", None),
        app=app,
        cac_object_list=cac_object_list
    )
    result = {
        "error": False,
        "message": "User logged in successfully",
        "resultset": login_result.to_dict(),
    }
    return resource_result(result, mime_type="application/json")


def get_user_data_by_username(
    username: str,
    request: Request,
    blueprint: Blueprint,
):
    """
    Get user data by username
    """
    dbo = GenericDbHelper(json_file="users", request=request,
                          blueprint=blueprint)
    result = get_default_resultset()
    user = dbo.fetch_row_by_entryname_raw('email', username)
    if user['error']:
        return user
    _ = DEBUG and \
        log_debug(f'MCP get_user_data_by_username | user: {user}')
    if user['resultset']:
        if user['resultset'].get('status', '1') == '1':
            token = token_encode(user['resultset'])
            result['resultset'] = {
                'token': token,
                '_id': get_id_as_string(user['resultset']),
            }
            return result
    result['error'] = True
    result['message'] = "User not found or inactive"
    return result


def mcp_authenticate_api_key(
    user_id: str,
    username: str,
    api_key: str,
    app: McpServerApp,
    cac_object_list: list,
):
    """
    Authenticate user with API key
    """
    if not api_key:
        raise ValueError("API key is required")
    if not username and not user_id:
        raise ValueError("Username or user_id is required")
    request = get_app_request(
        path="user/login",
        method="POST",
    )
    if MCP_MANDATORY_USER_ID and not user_id:
        blueprint = get_request_blueprint("login", app, request)
        user_data = get_user_data_by_username(
            username=username,
            request=request,
            blueprint=blueprint,
        )
        if user_data['error']:
            return user_data
        user_id = user_data['resultset']['_id']
    authorized_request = get_api_key_auth(
        request,
        api_key,
        user_id,
    )
    if isinstance(authorized_request, dict):
        return authorized_request
    set_tool_context(
        request=request,
        resultset={
            'user_id': user_id,
        },
        app=app,
        cac_object_list=cac_object_list
    )
    return get_default_resultset()


def get_access_token():
    """
    Get the access token
    """
    gatm = get_access_token_mcp()
    return gatm.token if gatm else None


def verify_app_context(
    app: McpServerApp,
    cac_object_list: list
):
    """
    Verify the app context
    """
    access_token = get_access_token()
    for cac in cac_object_list:
        if cac.app_context is None:
            if not os.environ.get("GS_API_KEY", access_token) or (
                not os.environ.get("GS_USER_ID") and
                not os.environ.get("GS_USER_NAME")
            ):
                raise ValueError("User not authenticated")
            else:
                result = mcp_authenticate_api_key(
                    user_id=os.environ.get("GS_USER_ID"),
                    username=os.environ.get("GS_USER_NAME"),
                    api_key=access_token or os.environ.get("GS_API_KEY"),
                    app=app,
                    cac_object_list=cac_object_list,
                )
                if result['error']:
                    raise ValueError(
                        result.get('error_message', "User not authenticated"))
    return True


def set_tool_context(request: Request, resultset: dict, app: McpServerApp,
                     cac_object_list: list):
    """
    Set the tool context
    """
    if resultset is None:
        raise ValueError("Resultset is None")
    if "token" not in resultset and "user_id" not in resultset:
        raise ValueError("token or user_id not found in resultset")
    if 'token' in resultset:
        jwt_token = resultset["token"]
        jws_token_data = jwt.decode(
            jwt_token,
            app.settings.APP_SECRET_KEY,
            algorithms="HS256",
        )
        _ = DEBUG and log_debug(
            'REQUEST_AUTHENTICATION@get_general_authorized_request'
            f' | jws_token_data = {jws_token_data}')
        authorized_request = get_authorized_request(request, jws_token_data)
    elif 'user_id' in resultset:
        auth_payload = AuthTokenPayload(public_id=resultset['user_id'])
        authorized_request = get_authorized_request(request, auth_payload)
    blueprint = get_request_blueprint("login", app, authorized_request)
    app_context = app_context_and_set_env(
        request=authorized_request, blueprint=blueprint)
    if app_context.has_error():
        raise ValueError("App context assignment error: " +
                         app_context.get_error())
    for cac in cac_object_list:
        cac.set(app_context)
    return True


def tool_result(result: str, other_data: dict = None) -> Dict[str, Any]:
    """
    Helper function to format tool results
    """
    if not other_data:
        other_data = {}
    error = "error" in result.lower()
    return {
        **other_data,
        "success": not error,
        "error": result if error else None,
        "message": None if error else result
    }


def resource_result(result: dict, mime_type: str = "text/plain"
                    ) -> Union[str, dict[str, Any]]:
    """
    Helper function to format resource results
    """
    if result["error"]:
        return json.dumps(result, indent=DEFAULT_JSON_INDENT)
    if mime_type == "application/json":
        return result["resultset"]
    return json.dumps(result["resultset"], indent=DEFAULT_JSON_INDENT)
