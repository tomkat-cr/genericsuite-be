"""
System users operations (CRUD, login, database test, super-admin creation)
"""
from typing import Optional

from genericsuite.util.framework_abs_layer import (
    Request,
    Response,
)
from genericsuite.util.jwt import (
    AuthorizedRequest,
)
from genericsuite.util.utilities import (
    return_resultset_jsonified_or_exception,
)
from genericsuite.flasklib.util.jwt import token_required
from genericsuite.flasklib.util.blueprint_one import BlueprintOne

from genericsuite.models.users.users import (
    test_connection_handler as test_connection_handler_model,
    login_user as login_user_model,
    super_admin_create as super_admin_create_model,
    get_current_user_data,
)
from genericsuite.util.app_context import save_all_users_params_files

bp = BlueprintOne('users', __name__, url_prefix='/users')


HEADER_CREDS_ENTRY_NAME = 'Authorization'
DEBUG = False


@bp.route('/test')
@token_required
def test_connection_handler(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """Connection handler test"""
    return test_connection_handler_model(request, other_params)


@bp.route('/login', methods=['GET', 'POST'])
def login_user(
    request: Request,
    other_params: Optional[dict] = None
) -> Response:
    """User login"""
    return login_user_model(
        request=request, blueprint=bp,
        other_params=other_params)


@bp.route('/supad-create', methods=['POST'])
def super_admin_create(
    request: Request,
    other_params: Optional[dict] = None
) -> Response:
    """Super admin user emergency creation"""
    return super_admin_create_model(
        request=request, blueprint=bp,
        other_params=other_params)


@bp.route('/current_user_d', methods=['GET'])
@token_required
def current_user_d(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """
    Get current authenticated user data
    """
    return get_current_user_data(request, bp, other_params)


@bp.route('/caujf', methods=['GET'])
def caujf(
    request: Request,
    other_params: Optional[dict] = None
) -> Response:
    """
    CAUJF: Create All User JSON Files (required for API Keys)
    """
    request = Request()
    request.set_properties()
    result = save_all_users_params_files()
    return return_resultset_jsonified_or_exception(result)
