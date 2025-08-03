from typing import Optional, Dict, Any
import json

import jwt

from genericsuite.models.users.users import (
    login_user as login_user_model,
)
from genericsuite.config.config_from_db import app_context_and_set_env
from genericsuite.util.app_logger import log_debug
from genericsuite.util.jwt import get_authorized_request

from genericsuite.mcplib.framework_abstraction import (
    Request,
    Response,
    Blueprint,
)
from genericsuite.mcplib.util.create_app import MCPServerApp


DEBUG: bool = False
DEFAULT_JSON_INDENT = 2


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
    app: MCPServerApp,
    request: Request,
) -> Blueprint:
    """
    Get the request blueprint
    """
    return Blueprint(name, app, request)


def mcp_login_user(
    app: MCPServerApp,
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


def verify_app_context(cac_object_list: list):
    """
    Verify the app context
    """
    for cac in cac_object_list:
        if cac.app_context is None:
            raise ValueError("User not authenticated")
    return True


def set_tool_context(request: Request, resultset: dict, app: MCPServerApp,
                     cac_object_list: list):
    """
    Set the tool context
    """
    if resultset is None:
        raise ValueError("Resultset is None")
    if "token" not in resultset:
        raise ValueError("Token not found in resultset")
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
    blueprint = get_request_blueprint("login", app, authorized_request)
    app_context = app_context_and_set_env(
        request=authorized_request, blueprint=blueprint)
    if app_context.has_error():
        raise ValueError("App context assignment error: " +
                         app_context.get_error_resultset())
    for cac in cac_object_list:
        cac.set(app_context)
    return True


def tool_result(result: str, oher_data: dict = None) -> Dict[str, Any]:
    """
    Helper function to format tool results
    """
    if not oher_data:
        oher_data = {}
    error = "error" in result.lower()
    return {
        **oher_data,
        "success": not error,
        "error": result if error else None,
        "message": None if error else result
    }


def resource_result(result: str, mime_type: str = "text/plain") -> str:
    """
    Helper function to format resource results
    """
    if result["error"]:
        return json.dumps(result, indent=DEFAULT_JSON_INDENT)
    if mime_type == "application/json":
        return result["resultset"]
    return json.dumps(result["resultset"], indent=DEFAULT_JSON_INDENT)
