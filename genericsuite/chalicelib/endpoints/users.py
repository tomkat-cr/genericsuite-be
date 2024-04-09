"""
System users operations (CRUD, login, database test, super-admin creation)
"""
from typing import Optional

# from chalice.app import Request, Response
from genericsuite.util.framework_abs_layer import Request, Response

from genericsuite.util.blueprint_one import BlueprintOne

from genericsuite.util.jwt import (
    request_authentication,
    AuthorizedRequest,
)

from genericsuite.models.users.users import (
    users_crud as users_crud_model,
    test_connection_handler as test_connection_handler_model,
    login_user as login_user_model,
    super_admin_create as super_admin_create_model,
    password_encripted as password_encripted_model,
)

bp = BlueprintOne(__name__)


HEADER_CREDS_ENTRY_NAME = 'Authorization'
DEBUG = False


@bp.route(
    '/',
    methods=['GET', 'POST', 'PUT', 'DELETE'],
    authorizor=request_authentication(),
)
def users_crud(request: AuthorizedRequest,
    other_params: Optional[dict] = None) -> Response:
    """ User's CRUD operations (create, read, update, delete) """
    return users_crud_model(request, other_params)


@bp.route(
    '/test',
    authorizor=request_authentication(),
)
def test_connection_handler(request: Request,
    other_params: Optional[dict] = None) -> Response:
    """Connection handler test"""
    return test_connection_handler_model(request, other_params)


@bp.route(
    '/login',
    methods=['GET', 'POST']
)
def login_user(request: Request,
    other_params: Optional[dict] = None) -> Response:
    """User login"""
    return login_user_model(request, other_params)


@bp.route(
    '/supad-create',
    methods=['POST']
)
def super_admin_create(request: Request,
    other_params: Optional[dict] = None) -> Response:
    """Super admin user emergency creation"""
    return super_admin_create_model(request, other_params)


@bp.route(
    '/pas-enc',
    methods=['POST'],
    # authorizor=request_authentication(),
)
def password_encripted(request: Request,
    other_params: Optional[dict] = None) -> Response:
    """Returns the given string as a encrypted password
    """
    return password_encripted_model(request, other_params)
