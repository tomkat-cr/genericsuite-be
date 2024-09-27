"""
JWT Library
"""
import base64
from typing import Callable
import datetime

import jwt
from pydantic import BaseModel

from genericsuite.util.framework_abs_layer import (
    Request, get_current_framework)

from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.utilities import (
    standard_error_return,
    get_default_resultset,
    get_id_as_string,
)
from genericsuite.config.config import Config

settings = Config()

# ----------------------- JWT -----------------------

EXPIRATION_MINUTES = 30
DEBUG = False


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
    Returns a function that performs request authentication with the specified
    audience list.

    Args:
        None

    Returns:
        Callable[[Request], AuthorizedRequest]: A function that performs
        request authentication.
    """
    def create_auth_request(request: Request) -> AuthorizedRequest:
        return get_general_authorized_request(request)
    return create_auth_request


def get_general_authorized_request(request: Request) -> AuthorizedRequest:
    """
    Get the authorized request from the request object.

    Args:
        request (Request): The request object.

    Returns:
        AuthorizedRequest: The authorized request.
    """
    if settings.HEADER_TOKEN_ENTRY_NAME not in request.headers:
        return standard_error_return('A valid token is missing')
    try:
        token_raw = request.headers[settings.HEADER_TOKEN_ENTRY_NAME]
        jwt_token = token_raw.replace('Bearer ', '')
        if DEBUG:
            log_debug(
                '||| REQUEST_AUTHENTICATION' +
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
        if DEBUG:
            log_debug(
                '||| REQUEST_AUTHENTICATION' +
                f' | jws_token_data = {jws_token_data}')

        if get_current_framework() == 'chalice':
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

        if DEBUG:
            log_debug(
                '||| REQUEST_AUTHENTICATION' +
                f' | authorized_request = {authorized_request}')
    except Exception as err:
        log_error(
            'REQUEST_AUTHENTICATION' +
            f' | Exception = {str(err)}')
        return standard_error_return('Token is invalid')
    return authorized_request


def token_encode(user):
    """
    Encode a JWT token for the given user.

    Args:
        user: The user for whom the token is being encoded.

    Returns:
        str: The encoded JWT token.
    """
    token = jwt.encode(
        {
            'public_id': get_id_as_string(user),
            'exp':
                datetime.datetime.utcnow() +
                datetime.timedelta(minutes=EXPIRATION_MINUTES)
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
