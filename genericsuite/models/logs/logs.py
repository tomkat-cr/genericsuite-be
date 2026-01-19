from typing import Optional

from pydantic import BaseModel

from genericsuite.util.framework_abs_layer import Response, BlueprintOne
from genericsuite.util.app_logger import (
    log_debug,
    log_error,
    log_info,
    log_warning,
)
from genericsuite.util.jwt import AuthorizedRequest
from genericsuite.util.utilities import (
    get_request_body,
    return_resultset_jsonified_or_exception,
)


class LogRequest(BaseModel):
    """ Log request """
    message: str
    log_type: str
    timestamp: int


def put_log(
    request: AuthorizedRequest,
    blueprint: BlueprintOne,
    other_params: Optional[dict] = None
) -> Response:
    """
    This endpoint is used to fetch food data from the FDA API.
    It takes in a request and other parameters and returns a response.

    :param request: The request object containing the request data.
    :param other_params: Any other parameters that may be needed.
    :return: A response object containing the response data.
    """
    if other_params is None:
        other_params = {}
    params = get_request_body(request)
    log_type = params.get('log_type').lower()
    message = params.get('message')

    if log_type == 'info':
        log_info(message)
    elif log_type == 'error':
        log_error(message)
    elif log_type == 'warning':
        log_warning(message)
    elif log_type == 'debug':
        log_debug(message)
    else:
        log_info(f"Unknown log type: {log_type} | message: {message}")

    return return_resultset_jsonified_or_exception(
        "Ok"
    )
