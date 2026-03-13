"""
JWT Library
"""
from typing import Callable, Union, Optional
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

DEBUG = False

EXPIRATION_MINUTES = os.environ.get('EXPIRATION_MINUTES', '30')

TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')
PARAMS_FILE_USER_FILENAME_TEMPLATE = os.environ.get(
    'PARAMS_FILE_USER_FILENAME_TEMPLATE', 'params_[user_id].json')

INVALID_TOKEN_ERROR_MESSAGE = 'Token is invalid'
OTHER_TOKEN_ERROR_MESSAGE = 'Token error'


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


def get_access_token_data(
        access_token: str,
        user_id: Optional[str] = None
) -> dict:
    """
    Get the access token data from the database.

    Args:
        access_token (str): The access token.
        user_id (str): The user ID.

    Returns:
        dict: The access token data.
    """
    try:
        dbo = GenericDbHelperSuper(json_file="users_api_keys")
        api_key_data = dbo.fetch_row_by_entryname_raw(
            'access_token', access_token)
        if api_key_data['error']:
            _ = DEBUG and log_error(
                'get_access_token_data | Table: users_api_keys | ' +
                'dbo.fetch_row_by_entryname_raw | Error:' +
                f' {str(api_key_data["error_message"])}')
            return error_resultset(api_key_data['error_message'])
        resultset = api_key_data['resultset']
        _ = DEBUG and log_debug(
            "get_access_token_data | Api Key resultset: "
            f"{resultset}")
        if not resultset:
            _ = DEBUG and log_error(
                'get_access_token_data | Api Key not found')
            return error_resultset(INVALID_TOKEN_ERROR_MESSAGE)
        if user_id and resultset['user_id'] != user_id:
            _ = DEBUG and log_error(
                "get_access_token_data | Api key user_id "
                f"'{resultset['user_id']}' does not match with "
                f"passed user_id: {user_id}")
            return error_resultset(INVALID_TOKEN_ERROR_MESSAGE)
        if resultset['active'] != '1':
            _ = DEBUG and log_error(
                'get_access_token_data | Api key is not active')
            return error_resultset(INVALID_TOKEN_ERROR_MESSAGE)

        user_id = resultset['user_id']
        try:
            dbo = GenericDbHelperSuper(json_file="users")
            user_data = dbo.fetch_row_raw(user_id)
            _ = DEBUG and log_debug(
                "get_access_token_data | user_id: "
                f"{user_id} | User resultset: {user_data['resultset']}")
            if user_data['error']:
                _ = DEBUG and log_error(
                    'get_access_token_data | Table: users | ' +
                    'dbo.fetch_row_raw(user_id) | Error:' +
                    f' {str(user_data["error_message"])}')
                return error_resultset(user_data['error_message'])
            if not user_data['resultset']:
                _ = DEBUG and log_error(
                    'get_access_token_data | User not found')
                return error_resultset(INVALID_TOKEN_ERROR_MESSAGE)
            if user_data['resultset'].get('status') != '1':
                _ = DEBUG and log_error(
                    'get_access_token_data | User is not active')
                return error_resultset(INVALID_TOKEN_ERROR_MESSAGE)

            user_data['valid_token'] = True
            user_data['user_id'] = get_id_as_string(user_data['resultset'])

        except Exception as err:
            _ = DEBUG and log_error(
                'get_access_token_data | Table: users | ' +
                'dbo.fetch_row_raw(user_id) | Exception:'
                f' {str(err)}')
            return error_resultset(INVALID_TOKEN_ERROR_MESSAGE)
        return user_data

    except Exception as err:
        _ = DEBUG and log_error(
            'get_access_token_data | Exception:'
            f' {str(err)}')
    return error_resultset(INVALID_TOKEN_ERROR_MESSAGE)


def get_api_key_auth(
    request: Request,
    access_token: str,
    user_id: Optional[str] = None,
) -> Union[AuthorizedRequest, dict]:
    """
    Get the authorized request from the request object.

    Args:
        request (Request): The request object.
        access_token (str): The access token (with or without the
            'Bearer ' prefix). Required for API Keys.
        user_id (str): The user ID specified as customer_id in the POST
            body. Optional for API Keys.

    Returns:
        Union[AuthorizedRequest, dict]: The authorized request or an error
            message.
    """
    if access_token.startswith('Bearer '):
        access_token = access_token[7:]
    access_token_data = get_access_token_data(access_token, user_id)
    if access_token_data['error']:
        return access_token_data
    if not access_token_data['valid_token']:
        return standard_error_return(INVALID_TOKEN_ERROR_MESSAGE)
    jws_token_data = AuthTokenPayload(
        public_id=access_token_data['user_id']
    )
    _ = DEBUG and log_debug(
        '||| get_api_key_auth' +
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
            'REQUEST_AUTHENTICATION | get_general_authorized_request' +
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
            'REQUEST_AUTHENTICATION | get_general_authorized_request'
            f' | jws_token_data = {jws_token_data}')
        authorized_request = get_authorized_request(request, jws_token_data)
        _ = DEBUG and log_debug(
            'REQUEST_AUTHENTICATION | get_general_authorized_request'
            f' | authorized_request = {authorized_request}')
    except Exception as err:
        error_message = str(err)
        if "signature has expired" in error_message.lower():
            log_error(
                f'REQUEST_AUTHENTICATION | get_general_authorized_request'
                f' | Exception: {error_message}')
            return standard_error_return(
                OTHER_TOKEN_ERROR_MESSAGE)
        # API Keys processing
        project_id = request.headers.get('x-project-id', '')
        _ = DEBUG and log_debug(
            'REQUEST_AUTHENTICATION | get_general_authorized_request'
            f'\n | project_id = {project_id}'
            f'\n | jwt_token = {jwt_token}'
            f'\n | headers = {request.headers}'
            f'\n | request = {request}')
        return get_api_key_auth(request, jwt_token, project_id)
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
