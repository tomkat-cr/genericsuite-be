"""
JWT token verification decorator for Flask.
"""
from typing import Callable
from functools import wraps

from flask import request

from genericsuite.util.jwt import get_general_authorized_request
from genericsuite.util.app_logger import log_debug

from genericsuite.flasklib.framework_abstraction import Request

DEBUG = True


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
        current_request = Request()
        current_request.set_properties()
        response = get_general_authorized_request(current_request)
        _ = DEBUG and log_debug(
            "@token_required decorator"
            f"\n | args: {args}"
            f"\n | kwargs: {kwargs}"
            f"\n | current_request: {current_request.to_dict()}"
            f"\n | response: {response}"
        )
        if isinstance(response, dict):
            # Invalid token or other error
            return response
        # Valid token received as AuthorizedRequest
        # if 'other_params' not in kwargs and len(args) == 0:
        #     kwargs['other_params'] = {}
        # return f(response, *args, **kwargs)
        return f(*args, **kwargs)
    return decorator
