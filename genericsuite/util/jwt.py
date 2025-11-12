"""
JWT Library
"""
from typing import Callable, Union
import os
import base64
import datetime
import secrets

import jwt
from pydantic import BaseModel

from genericsuite.util.framework_abs_layer import (
    Request,
    get_current_framework
)
from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.utilities import (
    standard_error_return,
    get_default_resultset,
    error_resultset,
    get_id_as_string,
)
from genericsuite.config.config import Config

from genericsuite.util.generic_db_helpers_super import \
    GenericDbHelperSuper

settings = Config()

# ----------------------- JWT -----------------------

DEBUG = True

EXPIRATION_MINUTES = os.environ.get('EXPIRATION_MINUTES', '30')

TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')
PARAMS_FILE_USER_FILENAME_TEMPLATE = os.environ.get(
    'PARAMS_FILE_USER_FILENAME_TEMPLATE', 'params_[user_id].json')

INVALID_TOKEN_ERROR_MESSAGE = 'Token is invalid'
USER_ID_REQUIRED_ERROR_MESSAGE = 'User ID is required to get access token data'


class AuthTokenPayload(BaseModel):
    """
    Represents the user's payload structure of the JWT token.
    """
    public_id: str


class AuthorizedRequest(Request):
    """
    Represents the AuthorizedRequest payload structure of the JWT token,
    containing the authenticated user's data.
    """
    user: AuthTokenPayload


def request_authentication() -> Callable[[Request], AuthorizedRequest]:
    """
    Returns a function that performs request authentication.

    Args:
        None

    Returns:
        Callable[[Request], AuthorizedRequest]: A function that performs
        request authentication.
    """
    def create_auth_request(request: Request) -> AuthorizedRequest:
        return get_general_authorized_request(request)
    return create_auth_request


def get_authorized_request(
    request: Request,
    jws_token_data: AuthTokenPayload
) -> AuthorizedRequest:
    """
    Get the authorized request from the request object, according to the
    current framework.
    """
    if get_current_framework() == 'flask':
        authorized_request = AuthorizedRequest(
            # # type: ignore[attr-defined]
            # event_dict=request.to_original_event(),
            # # type: ignore[attr-defined]
            # lambda_context=request.lambda_context,
            # type: ignore[attr-defined]
            user=jws_token_data
        )
        authorized_request.set_properties()
    elif get_current_framework() == 'chalice':
        authorized_request = AuthorizedRequest(
            # type: ignore[attr-defined]
            event_dict=request.to_original_event(),
            # type: ignore[attr-defined]
            lambda_context=request.lambda_context,
        )
        # Authentication token data
        authorized_request.user = jws_token_data
    else:
        authorized_request = AuthorizedRequest(
            # type: ignore[attr-defined]
            event_dict=request.to_original_event(),
            # type: ignore[attr-defined]
            lambda_context=request.lambda_context,
            # Authentication token data
            user=jws_token_data,
        )
    return authorized_request


def generate_access_token(length=64):
    """
    Generate an access token.

    Example usage:
        access_token = generate_access_token()
        print(f"Generated Access Token: {access_token}")
    """
    return secrets.token_hex(length)


def get_access_token_data(access_token: str, user_id: str = None) -> dict:
    """
    Get the access token data from the database.

    Args:
        access_token (str): The access token.
        user_id (str): The user ID.

    Returns:
        dict: The access token data.
    """
    if not user_id:
        return error_resultset(USER_ID_REQUIRED_ERROR_MESSAGE)
    dbo = GenericDbHelperSuper(json_file="users")
    user_data = dbo.fetch_row_raw(user_id)
    if user_data['error']:
        return error_resultset(user_data['error_message'])
    try:
        # Check if the access token is valid
        user_data['valid_token'] = False

        log_debug(f'JWT.py | get_access_token_data | user_data: {user_data}')

        resultset = user_data['resultset']
        for api_key in resultset.get('users_api_keys', []):
            if api_key['access_token'] == access_token and \
               api_key['active'] == '1':
                user_data['valid_token'] = True
                break
        if user_data['valid_token']:
            user_data['user_id'] = get_id_as_string(resultset)
            return user_data
    except Exception as err:
        _ = DEBUG and log_error(
            'REQUEST_AUTHENTICATION@get_api_key_auth | Exception:'
            f' {str(err)}')
    return error_resultset(INVALID_TOKEN_ERROR_MESSAGE)


def get_api_key_auth(
    request: Request,
    user_id: str,
    access_token: str
) -> Union[AuthorizedRequest, dict]:
    """
    Get the authorized request from the request object.

    Args:
        request (Request): The request object.
        user_id (str): The user ID specified as customer_id in the POST
            body.
        access_token (str): The access token (without 'Bearer ' prefix).
            (required for API Keys)

    Returns:
        Union[AuthorizedRequest, dict]: The authorized request or an error
            message.
    """
    access_token_data = get_access_token_data(access_token, user_id)
    if access_token_data['error']:
        return access_token_data
    if not access_token_data['valid_token']:
        return standard_error_return(INVALID_TOKEN_ERROR_MESSAGE)
    jws_token_data = AuthTokenPayload(
        public_id=access_token_data['user_id']
    )
    _ = DEBUG and log_debug(
        '||| REQUEST_AUTHENTICATION@get_api_key_auth' +
        f' | jws_token_data = {jws_token_data}')
    authorized_request = get_authorized_request(request, jws_token_data)
    return authorized_request


def get_general_authorized_request(request: Request
                                   ) -> Union[AuthorizedRequest, dict]:
    """
    Get the authorized request from the request object.

    Args:
        request (Request): The request object.

    Returns:
        Union[AuthorizedRequest, dict]: The authorized request or an error
            message.
    """
    if settings.HEADER_TOKEN_ENTRY_NAME not in request.headers:
        return standard_error_return('A valid token is missing')
    try:
        token_raw = request.headers[settings.HEADER_TOKEN_ENTRY_NAME]
        jwt_token = token_raw.replace('Bearer ', '')
        _ = DEBUG and log_debug(
            'REQUEST_AUTHENTICATION@get_general_authorized_request' +
            '\n | HEADER_TOKEN_ENTRY_NAME: ' +
            f'{settings.HEADER_TOKEN_ENTRY_NAME}' +
            f'\n | token_raw: {token_raw}' +
            f'\n | jwt_token: {jwt_token}' +
            # f'\n | settings.APP_SECRET_KEY: {settings.APP_SECRET_KEY}' +
            '\n')
        jws_token_data = jwt.decode(
            jwt_token,
            settings.APP_SECRET_KEY,
            algorithms="HS256",
        )
        _ = DEBUG and log_debug(
            'REQUEST_AUTHENTICATION@get_general_authorized_request'
            f' | jws_token_data = {jws_token_data}')
        authorized_request = get_authorized_request(request, jws_token_data)
        _ = DEBUG and log_debug(
            'REQUEST_AUTHENTICATION@get_general_authorized_request'
            f' | authorized_request = {authorized_request}')
    except Exception as err:
        # API Keys processing
        project_id = request.headers.get('x-project-id', '')
        _ = DEBUG and log_debug(
            'REQUEST_AUTHENTICATION@get_general_authorized_request'
            f'\n | project_id = {project_id}'
            f'\n | jwt_token = {jwt_token}'
            f'\n | headers = {request.headers}'
            f'\n | request = {request}')
        if project_id and jwt_token:
            return get_api_key_auth(request, project_id, jwt_token)
        _ = DEBUG and log_error(
            f'REQUEST_AUTHENTICATION@get_general_authorized_request'
            f' | Exception: {str(err)}')
        return standard_error_return(INVALID_TOKEN_ERROR_MESSAGE)
    return authorized_request


def token_encode(user):
    """
    Encode a JWT token for the given user.

    Args:
        user: The user for whom the token is being encoded.

    Returns:
        str: The encoded JWT token.
    """
    # Validate EXPIRATION_MINUTES can be converted to int
    try:
        expiration_minutes = int(EXPIRATION_MINUTES)
    except ValueError:
        expiration_minutes = 30
    token = jwt.encode(
        {
            'public_id': get_id_as_string(user),
            'exp':
                datetime.datetime.now(datetime.timezone.utc) +
                datetime.timedelta(minutes=expiration_minutes)
        },
        settings.APP_SECRET_KEY,
        algorithm="HS256"
    )
    return token


def get_basic_auth(authorization):
    """
    Decode and extract user and password from the Basic Authorization header.

    Args:
        authorization (str): The Basic Authorization header.
        e.g. authorization = app.current_request.headers.get('Authorization',
                                                             '')

    Returns:
        dict: A dictionary containing the user and password.
    """
    response = get_default_resultset()
    if not authorization.startswith('Basic '):
        response['error'] = True
        response['error_message'] = 'Authorization Required'
        response['status_code'] = 401
        # return Response(body='Authorization Required', status_code=401)
        return response

    credentials = authorization[len('Basic '):]
    decoded_credentials = base64.b64decode(
        credentials.encode('ascii')
    ).decode('ascii')
    user, password = decoded_credentials.split(':', 1)
    response['resultset'] = {
        'user': user,
        'password': password,
    }
    return response
