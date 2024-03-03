"""
JWT Library
"""
# from bson.json_util import dumps
import base64
from typing import Callable, List
import datetime

import jwt

# from chalice.app import Request
from genericsuite.util.framework_abs_layer import Request

from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.utilities import (
    standard_error_return,
    get_default_resultset,
    get_id_as_string,
)
from genericsuite.config.config import Config

settings = Config()

# import logging
# logger = logging.getLogger(settings.APP_NAME)

# ----------------------- JWT -----------------------

EXPIRATION_MINUTES = 30
DEBUG = False


class TokenPayload:
    """
    Represents the user's payload structure of the JWT token.
    """
    public_id: str


class AuthorizedRequest(Request):
    """
    Represents the AuthorizedRequest payload structure of the JWT token,
    containing the authenticated user's data.
    """
    user: TokenPayload


def _request_authentication_with_audience(
    audiences: List[str]
) -> Callable[[Request], AuthorizedRequest]:
    """
    Returns a function that performs request authentication with the specified
    audience list.

    Args:
        audiences (List[str]): The list of audiences to validate the token
        against.

    Returns:
        Callable[[Request], AuthorizedRequest]: A function that performs
        request authentication.
    """
    def _create_auth_request(request: Request) -> AuthorizedRequest:
        if settings.HEADER_TOKEN_ENTRY_NAME not in request.headers:
            # raise UnauthorizedQuery('Missing Authorization Token')
            return standard_error_return('A valid token is missing')
        try:
            token_raw = request.headers[settings.HEADER_TOKEN_ENTRY_NAME]
            token = token_raw.replace('Bearer ', '')
            if DEBUG:
                log_debug('||| _REQUEST_AUTHENTICATION_WITH_AUDIENCE' +
                    '\n | HEADER_TOKEN_ENTRY_NAME: ' +
                    f'{settings.HEADER_TOKEN_ENTRY_NAME}' +
                    f'\n | token_raw: {token_raw}' +
                    f'\n | token: {token}' +
                    # f'\n | settings.APP_SECRET_KEY: {settings.APP_SECRET_KEY}' +
                    f'\n | audiences (Deprecated in PYJWT v3): {audiences}' )
            token_payload = jwt.decode(
                token,
                settings.APP_SECRET_KEY,
                algorithms="HS256",
                # audiences=audiences,
            )
            if DEBUG:
                log_debug('||| _REQUEST_AUTHENTICATION_WITH_AUDIENCE' +
                    f' | token_payload = {token_payload}')
            auth_request = AuthorizedRequest(
                # type: ignore[attr-defined]
                request.to_original_event(),
                # type: ignore[attr-defined]
                lambda_context=request.lambda_context
            )
            auth_request.user = token_payload
            if DEBUG:
                log_debug('||| _REQUEST_AUTHENTICATION_WITH_AUDIENCE' +
                    f' | auth_request = {auth_request}')
        except Exception as err:
            log_error('_REQUEST_AUTHENTICATION_WITH_AUDIENCE' +
                f' | Exception = {str(err)}')
            # raise e
            return standard_error_return('Token is invalid')
        return auth_request
    return _create_auth_request


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
    audience_list = settings.FRONTEND_AUDIENCE.split(',')
    return _request_authentication_with_audience(audience_list)


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
