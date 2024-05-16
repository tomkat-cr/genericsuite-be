"""
Current user data module
"""
from typing import Any
from genericsuite.util.framework_abs_layer import get_current_framework
from genericsuite.util.generic_db_helpers import GenericDbHelper
from genericsuite.util.jwt import AuthorizedRequest
from genericsuite.util.utilities import (
    get_default_resultset,
    error_resultset,
)

DEBUG = False
NON_AUTH_REQUEST_USER_ID = "[N/A/R]"

def get_curr_user_id(request: AuthorizedRequest) -> str:
    """Get the current user ID"""
    user_id = None
    authorized_request = hasattr(request, 'user') and request.user
    if authorized_request:
        if get_current_framework() == 'chalice':
            user_id = request.user.get("public_id")
        else:
            user_id = request.user.public_id
    else:
        # Is a non-authorization request, so returns the identificator
        # 'N/A/R' meaning "Non-Authorization Request"
        user_id = NON_AUTH_REQUEST_USER_ID
    return user_id


def get_curr_user_data(
    request: AuthorizedRequest,
    blueprint: Any
) -> dict:
    """Get the current user data."""
    user_response = get_default_resultset()
    user_id = get_curr_user_id(request)
    if not user_id:
        user_response = error_resultset(
            "No user ID in authorization header", "GCUD-E010")
    elif user_id == NON_AUTH_REQUEST_USER_ID:
        # Is a non-authorization request, so returns
        # the 'resultset' as a empty dict and no error
        pass
    else:
        dbo = GenericDbHelper(json_file="users", request=request, blueprint=blueprint)
        user_response = dbo.fetch_row_raw(user_id, {'passcode': 0})
    return user_response
