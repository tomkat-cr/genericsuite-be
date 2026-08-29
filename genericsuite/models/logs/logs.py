from pydantic import BaseModel, Field, field_validator

from genericsuite.util.framework_abs_layer import Response
from genericsuite.util.app_logger import (
    log_debug,
    log_error,
    log_info,
    log_warning,
    sanitize_log_message,
)
from genericsuite.util.utilities import (
    # get_request_body,
    return_resultset_jsonified_or_exception,
)


class LogRequest(BaseModel):
    """ Log request """
    message: str = Field(min_length=10, max_length=5000)
    log_type: str = Field(min_length=4, max_length=10)
    timestamp: int = Field(ge=0)
    hp: str = Field(default="")

    @field_validator("message", "log_type", "hp", mode="before")
    @classmethod
    def strip_str(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("timestamp", mode="before")
    @classmethod
    def convert_timestamp(cls, v: object) -> object:
        return int(v) if isinstance(v, str) else v


def put_log(
    data: LogRequest
) -> Response:
    """
    This endpoint is used to receive and process log messages from clients.
    It takes in a request containing a log message and its type.

    :param request: The request object containing the request data.
    :param other_params: Any other parameters that may be needed.
    :return: A response object containing the response data.
    """
    log_type = (data.log_type or 'info').lower()
    message = sanitize_log_message(data.message)

    if data.hp:
        return return_resultset_jsonified_or_exception(
            {
                "error": False,
                "resultset": "Ok",
            }
        )

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
        {
            "error": False,
            "resultset": "Ok",
        }
    )
