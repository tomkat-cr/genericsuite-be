"""
System users operations (CRUD, login, database test, super-admin creation)
"""
from typing import Optional

from genericsuite.mcplib.framework_abstraction import (
    Response,
)
from genericsuite.mcplib.util.create_app import create_app
from genericsuite.mcplib.util.utilities import (
    get_app_request,
    get_request_blueprint,
    mcp_login_user,
)

from genericsuite.models.users.users import (
    test_connection_handler as test_connection_handler_model,
    super_admin_create as super_admin_create_model,
    get_current_user_data,
)


DEBUG = False

app = create_app()
mcp = app.mcp


@mcp.tool()
async def test(
    other_params: Optional[dict] = None
) -> Response:
    """Connection handler test"""
    return test_connection_handler_model(app.request, other_params)


@mcp.tool()
async def login(
    username: str,
    password: str,
    other_params: Optional[dict] = None
) -> Response:
    """
    User login
    """
    return mcp_login_user(app, username, password, other_params)


@mcp.tool()
async def supad_create(
    username: str,
    password: str,
    other_params: Optional[dict] = None
) -> Response:
    """
    Super admin user creation
    """
    if other_params is None:
        other_params = {}
    other_params['username'] = username
    other_params['password'] = password
    request = get_app_request(
        path="user/supad_create",
        method="POST",
    )
    blueprint = get_request_blueprint("supad_create", app, request)
    return super_admin_create_model(
        request=request,
        blueprint=blueprint,
        other_params=other_params)


@mcp.tool()
async def current_user_d(
    other_params: Optional[dict] = None
) -> Response:
    """
    Get current authenticated user data
    """
    request = get_app_request(
        path="user/current_user_data",
        method="GET",
    )
    blueprint = get_request_blueprint("current_user_data", app, request)
    return get_current_user_data(
        request=request,
        blueprint=blueprint,
        other_params=other_params)
