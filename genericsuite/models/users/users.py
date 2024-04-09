"""
System users operations (CRUD, login, database test, super-admin creation)
"""
from typing import Optional
import json

# from chalice.app import Request, Response
from genericsuite.util.framework_abs_layer import Request, Response

# from genericsuite.util.blueprint_one import BlueprintOne
from genericsuite.util.db_abstractor import (
    set_db_request,
    test_connection,
)
from genericsuite.util.generic_db_helpers import (
    GenericDbHelper,
)
from genericsuite.util.app_logger import log_debug
from genericsuite.util.jwt import (
    # request_authentication,
    token_encode,
    get_basic_auth,
    AuthorizedRequest,
)
from genericsuite.util.passwords import Passwords
from genericsuite.util.utilities import (
    return_resultset_jsonified_or_exception,
    get_default_resultset,
    get_request_body,
    get_id_as_string,
)
from genericsuite.config.config import Config
from genericsuite.util.generic_endpoint_helpers import GenericEndpointHelper
from genericsuite.config.config_from_db import app_context_and_set_env
from genericsuite.constants.const_tables import get_constant


# bp = BlueprintOne(__name__)


HEADER_CREDS_ENTRY_NAME = 'Authorization'
DEBUG = False


# @bp.route(
#     '/',
#     methods=['GET', 'POST', 'PUT', 'DELETE'],
#     authorizor=request_authentication(),
# )
def users_crud(request: AuthorizedRequest,
    other_params: Optional[dict] = None) -> Response:
    """ User's CRUD operations (create, read, update, delete) """
    if not other_params:
        other_params = {}
    # Set environment variables from the database configurations.
    app_context = app_context_and_set_env(request)
    if app_context.has_error():
        return return_resultset_jsonified_or_exception(
            app_context.get_error_resultset()
        )
    # User's CRUD operations
    ep_helper = GenericEndpointHelper(
        app_context=app_context,
        json_file="users",
        url_prefix=__name__,
    )
    return ep_helper.generic_crud_main()


# @bp.route(
#     '/test',
#     authorizor=request_authentication(),
# )
def test_connection_handler(request: Request,
    other_params: Optional[dict] = None) -> Response:
    """Connection handler test"""
    if not other_params:
        other_params = {}
    result = get_default_resultset()
    set_db_request(request)
    result['resultset']['collections'] = json.loads(test_connection())
    if DEBUG:
        log_debug(f'Test DB connection | request: {request}')
    return return_resultset_jsonified_or_exception(result)


# @bp.route(
#     '/login',
#     methods=['GET', 'POST']
# )
def login_user(request: Request,
    other_params: Optional[dict] = None) -> Response:
    """User login"""
    if not other_params:
        other_params = {}
    psw_class = Passwords()
    dbo = GenericDbHelper(json_file="users", request=request)
    if DEBUG:
        log_debug(f'login_user | request: {request}')
        # log_debug('login_user | bp.current_request.to_dict(): ' +
        #           f'{bp.current_request.to_dict()}')
    result = get_default_resultset()
    basic_auth_data = get_basic_auth(
        request.headers.get(HEADER_CREDS_ENTRY_NAME, '')
    )
    if DEBUG:
        log_debug(f'login_user | basic_auth_data: {basic_auth_data}')
    if basic_auth_data['error']:
        # 'Could not verify [L1]'
        result['error_message'] = basic_auth_data['error_message']
        return return_resultset_jsonified_or_exception(
            result=result,
            http_error=basic_auth_data['status_code']
        )
    username = basic_auth_data['resultset']['user']
    password = basic_auth_data['resultset']['password']
    user = dbo.fetch_row_by_entryname_raw('email', username)
    if user['error']:
        return return_resultset_jsonified_or_exception(user)
    if DEBUG:
        log_debug(f'login_user | user[resultset]: {user}')
    if user['resultset']:
        if 'passcode' in user['resultset']:
            if psw_class.verify_password(user['resultset']['passcode'],
                                         password):

                if user['resultset'].get('status', '1') == '1':
                    token = token_encode(user['resultset'])
                    result['resultset'] = {
                        'token': token,
                        '_id': get_id_as_string(user['resultset']),
                        'firstname': user['resultset']['firstname'],
                        'lastname': user['resultset']['lastname'],
                        'email': user['resultset']['email'],
                        'username': user['resultset']['email'],
                    }
                else:
                    result['error_message'] = get_constant("ERROR_MESSAGES",
                                                           "ACCOUNT_INACTIVE")
            else:
                result['error_message'] = 'Could not verify [L3]'
        else:
            result['error_message'] = 'Inconsistency [L4]'
    else:
        result['error_message'] = 'Could not verify [L2]'
    if DEBUG:
        log_debug(f'login_user | FINAL result: {result}')
    return return_resultset_jsonified_or_exception(result, 401)


# @bp.route(
#     '/supad-create',
#     methods=['POST']
# )
def super_admin_create(request: Request,
    other_params: Optional[dict] = None) -> Response:
    """Super admin user emergency creation"""
    # Set environment variables from the database configurations.
    app_context = app_context_and_set_env(request)
    if app_context.has_error():
        return return_resultset_jsonified_or_exception(
            app_context.get_error_resultset()
        )
    settings = Config(app_context)
    if not other_params:
        other_params = {}
    psw_class = Passwords()
    dbo = GenericDbHelper(json_file="users", request=request)
    result = get_default_resultset()
    basic_auth_data = get_basic_auth(
        request.headers.get(HEADER_CREDS_ENTRY_NAME, '')
    )
    if DEBUG:
        log_debug(f'supad-create | basic_auth_data: {basic_auth_data}')
    if basic_auth_data['error']:
        result['error_message'] = basic_auth_data['error_message']
        return return_resultset_jsonified_or_exception(
            result=result,
            http_error=basic_auth_data['status_code']
        )

    username = basic_auth_data['resultset']['user']
    password = basic_auth_data['resultset']['password']
    if not username or not password:
        result['error_message'] = 'Could not verify [SAC1]'
    elif username != settings.APP_SUPERADMIN_EMAIL:
        result['error_message'] = 'Could not verify [SAC2]'
    elif not psw_class.verify_password(
         psw_class.encrypt_password(settings.APP_SECRET_KEY), password
         ):
        result['error_message'] = 'Could not verify [SAC3]'

    if result['error_message']:
        return return_resultset_jsonified_or_exception(result)

    user = dbo.fetch_row_by_entryname_raw('email', username)
    if user['error']:
        return return_resultset_jsonified_or_exception(user)

    if user['resultset']:
        result['error_message'] = 'User already exists [SAC4]'
    else:
        request_body = {
            "firstname": "Admin",
            "lastname": "Super",
            "superuser": "1",
            "status": "1",
            "plan": "premium",
            "language": "en",
            'email':  username,
            'passcode': password,
            "creation_date": 1635033994,
            "update_date": 1635033994,
            "birthday": -131760000,
        }
        for field in dbo.get_mandatory_fields(record=request_body,
                                              is_create=True):
            if field not in request_body:
                request_body[field] = ''
        result = dbo.create_row(request_body)

    return return_resultset_jsonified_or_exception(result)


# @bp.route(
#     '/pas-enc',
#     methods=['POST'],
#     # authorizor=request_authentication(),
# )
def password_encripted(request: Request,
    other_params: Optional[dict] = None) -> Response:
    """Returns the given string as a encrypted password
    """
    if not other_params:
        other_params = {}
    psw_class = Passwords()
    request_body = get_request_body(request)
    result = get_default_resultset()
    result['resultset'] = {}
    if request_body.get('passwd', None) is not None:
        result['resultset'] = {
            # 'orig_pass': request_body.get('passwd'),
            'enc_pass': psw_class.encrypt_password(request_body.get('passwd'))
        }
    else:
        result['error_message'] = 'Parameter not received [PSEN1]'
    return return_resultset_jsonified_or_exception(result)
