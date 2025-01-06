"""
JWT token verification decorator for Flask.
"""
from typing import Callable
from functools import wraps

from genericsuite.util.jwt import (
    get_general_authorized_request,
    AuthorizedRequest,
)
from genericsuite.util.app_logger import log_debug

DEBUG = False


def token_required(f: Callable) -> Callable:
    """
    Decorator for verifying the JWT token in Flask requests.

    Args:
        f (Callable): The function to be decorated.

    Returns:
        Callable: The decorated function.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        # The current request is in args[0]...
        response = get_general_authorized_request(args[0])
        _ = DEBUG and log_debug(
            "@token_required decorator"
            f"\n | args: {args}"
            f"\n | kwargs: {kwargs}"
            f"\n | response: {response}"
        )
        if not isinstance(response, AuthorizedRequest):
            _ = DEBUG and log_debug(
                "@token_required decorator"
                "\n | Invalid token or other error\n"
            )
            return response
        # Valid token received as AuthorizedRequest
        return f(response, **kwargs)
    return decorator
