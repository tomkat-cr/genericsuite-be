"""
General Utilities
"""
from typing import Optional, Match, AnyStr, Any, Union
import os
import re
import sys
import traceback
import base64

from mimetypes import MimeTypes

# from flask import jsonify, make_response
# from flask_cors import cross_origin

# from chalice.app import Response, Request
from genericsuite.util.framework_abs_layer import Response, Request

from genericsuite.util.app_logger import log_error, log_debug

# Email validation regular expression
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# send_file() mode
SEND_FILE_AS_BINARY = False

DEBUG = False


def check_email(email) -> Optional[Match[AnyStr]]:
    """ Check that an email address is valid"""
    return re.fullmatch(EMAIL_REGEX, email)


def email_verification(data, email_fields):
    """
    Verifies the email fields in the data.

    Args:
        data (dict): The data containing the email fields to be verified.
        email_fields (list): The list of email fields to be verified.

    Returns:
        dict: The resultset containing the error message if any
        email field is invalid.
    """
    resultset = get_default_resultset()
    for email_field in email_fields:
        if email_field not in data:
            resultset['error_message'] = \
                'error: Email wasn\'t specified [EMV1].'
            break
        if data[email_field] == 'foo@baz.com' \
                and not (
                    'pytest_run' in data
                    and data['pytest_run'] == 1
                ):
            resultset['error_message'] = \
                f"error: {data[email_field]} is invalid [EMV2]."
            break
        if not check_email(data[email_field]):
            resultset['error_message'] = \
                f"error: Malformed email {data[email_field]} [EMV3]."
            break
    return resultset


def get_file_size(file_size, measure="mb"):
    """Returns the file size in the given measure"""
    result = f'{file_size} bytes'
    measure = measure.lower()
    if measure == "kb":
        result = f'{file_size / 1024:.2f} Kb'
    if measure == "mb":
        result = f'{file_size / (1024 * 1024):.2f} Mb'
    if measure == "gb":
        result = f'{file_size / (1024 * 1024 * 1024):.2f} Gb'
    if measure == "tb":
        result = f'{file_size / (1024 * 1024 * 1024 * 1024):.2f} Tb'
    if measure == "pb":
        result = f'{file_size / (1024 * 1024 * 1024 * 1024 * 1024):.2f} Pb'
    return result


def get_default_resultset() -> dict:
    """Returns an standard base resultset, to be used in the building
       of responses to the outside world
    """
    resultset = {
        'error': False,
        'error_message': None,
        'totalPages': None,
        'resultset': {}
    }
    return resultset


def error_resultset(
    error_message: str,
    message_code: str = ''
) -> dict:
    """
    Return an error resultset.
    """
    message_code = f" [{message_code}]" if message_code else ''
    result = get_default_resultset()
    result['error'] = True
    result['error_message'] = f"{error_message}{message_code}"
    return result


def return_resultset_jsonified_or_exception(
    result: dict,
    http_error: int = 400,
    headers: dict = None,
) -> Response:
    """Standard way to return results to to outside world.
       If there's an error, returns a header with an HTTP error code
    """
    if not headers:
        headers = {}
    if result['error'] or result['error_message']:
        if DEBUG:
            log_debug(
                'return_resultset_jsonified_or_exception |' +
                f' ERROR error_message: {result["error_message"]}' +
                f' | http_error: {http_error}'
            )
        return standard_error_return(
            error_message=result['error_message'],
            error_code=http_error,
            headers=headers,
        )
    return Response(body=result, status_code=200, headers=headers)


def get_standard_base_exception_msg(
    err: Any,
    message_code: Optional[Union[str, None]] = 'NO_E_CODE'
) -> str:
    """
    When a BaseException is fired, use this method to return
    a standard error message
    """
    message_code = f" [{message_code}]" if message_code else ''
    response = f"Unexpected Error: {err}, {type(err)}{message_code}"
    log_error(response)
    log_error(format_stacktrace())
    return response


def send_file(
    file_to_send: str,
    download_name: str = None,
) -> Response:
    """
    Send the contents of a file to the client.
    """
    if SEND_FILE_AS_BINARY:
        return send_file_as_bin(
            file_to_send=file_to_send,
            download_name=download_name,
        )
    return send_file_text_text(
        file_to_send=file_to_send,
        download_name=download_name,
    )


def send_file_as_bin(
    file_to_send: str,
    download_name: str = None,
) -> Response:
    """
    Send the contents of a file to the client as binary.
    """
    if not download_name:
        download_name = os.path.basename(file_to_send)
    # Verify file existence
    if not os.path.exists(file_to_send):
        return standard_error_return(
            error_message=f'File not found: {file_to_send}',
            error_code=404,
        )
    # Create a Chalice Response object to send the file back to the client
    with open(file_to_send, 'rb') as file_handler:
        file_data = file_handler.read()
    headers = {
        'Content-Type': get_mime_type(file_to_send),
        # 'Content-Type': 'application/octet-stream',
        'Content-Disposition': f'attachment; filename="{download_name}"',
    }
    if DEBUG:
        log_debug("SEND_FILE_AS_BIN" +
                  f"\n | file_to_send: {file_to_send}" +
                  f"\n | download_name: {download_name}" +
                  f"\n | headers: {headers}")
        # log_debug("2) SEND_FILE | bin_to_b64_to_ascii(file_data):\n" +
        #           f"{bin_to_b64_to_ascii(file_data)}")

    return Response(
        body=file_data,
        status_code=200,
        headers=headers
    )


def send_file_text_text(
    file_to_send: str,
    download_name: str = None,
) -> Response:
    """
    Send the contents of a file to the client as Base64 encoded text.
    """
    if not download_name:
        download_name = os.path.basename(file_to_send)
    # Verify file existence
    if not os.path.exists(file_to_send):
        return standard_error_return(
            error_message=f'File not found: {file_to_send}',
            error_code=404,
        )
    # Create a Chalice Response object to send the file back to the client
    with open(file_to_send, 'rb') as file_handler:
        file_data = file_handler.read()
    file_encoded = bin_to_b64_to_ascii(file_data)

    headers = {
        'Content-Type': "text/text",
        'Content-Disposition': f'attachment; filename="{download_name}"',
    }
    if DEBUG:
        log_debug("SEND_FILE_TEXT_TEXT" +
                  f"\n | file_to_send: {file_to_send}" +
                  f"\n | download_name: {download_name}" +
                  f"\n | headers: {headers}")
        log_debug(f"2) SEND_FILE |file_encoded:\n{file_encoded}")
    return Response(
        body=file_encoded,
        status_code=200,
        headers=headers
    )


def bin_to_b64_to_ascii(data):
    """
    Do the conversion that Chalice does for binary files...
    """
    _ = DEBUG and log_debug(f"BIN_TO_B64_TO_ASCII | data:\n{data}")
    data = base64.b64encode(data)
    _ = DEBUG and log_debug("BIN_TO_B64_TO_ASCII | " +
                            f"base64.b64encode(data):\n{data}")
    return data.decode('ascii')


def format_stacktrace() -> str:
    """Returns the stack trace summarized

    Returns:
        str: the last 2 files and the exception message
             from the stack trace
    """
    parts = ["Traceback (most recent call last):\n"]
    parts.extend(traceback.format_stack(limit=25)[:-2])
    parts.extend(traceback.format_exception(*sys.exc_info())[1:])
    return "".join(parts)


# @cross_origin(supports_credentials=True)
def standard_error_return(
    error_message: str,
    error_code: int = 401,  # Unauthorized
    headers: dict = None
) -> Response:
    """Returns a standard error response"""
    if not headers:
        headers = {'WWW.Authentication': 'Basic realm: "login required"'}
    # return make_response(error_message, error_code, headers)
    return Response(
        body=error_message, status_code=error_code, headers=headers
    )


def method_not_allowed() -> Response:
    """Return a response with 405 Method Not Allowed"""
    return Response(body='Method Not Allowed', status_code=405)


def get_query_params(request: Request) -> dict:
    """Returns the query parameters (Chalice)"""
    query_params = request.to_dict()['query_params']
    if query_params is None:
        query_params = {}
    return query_params


def get_request_body(request: Request) -> dict:
    """Returns the request body (Chalice)"""
    try:
        request_body = request.json_body
    except BaseException:
        request_body = dict()
    return request_body


def is_an_url(element_url_or_path: str):
    """ Returns True if the string is an URL"""
    return element_url_or_path.startswith(
        ("http://", "https://", "ftp://", "file://")
    )


def sort_list_of_dicts(data: list[dict], column_name: str, direction: str):
    """
    Sorts a list of dictionaries by the specified column name and direction.

    Args:
        data (list[dict]): The list of dictionaries to be sorted.
        column_name (str): The name of the column to sort by.
        direction (str): The direction of the sort, either "asc" or "desc".

    Returns:
        list[dict]: The sorted list of dictionaries.
    """

    if DEBUG:
        log_debug("")
        log_debug(f"sort_list_of_dicts | data: {data}")
    sorted_data = sorted(
        data,
        key=lambda x: str(x.get(column_name)).upper(),
        reverse=direction == "desc"
    )
    if DEBUG:
        log_debug(f"sort_list_of_dicts | sorted_data: {sorted_data}")
        log_debug("")
    return sorted_data


# Previouslly: get_user_id_as_string
def get_id_as_string(row):
    """
    Returns the Object(_ID) of a row as a string.

    Args:
        row (dict): The row containing the ID (MongoDb).

    Returns:
        str: The ID of the row as a string.
    """
    return str(row['_id'])


def get_default_value(entryname, dict_obj, default_value):
    """
    Try to get the entryname in the dict, if not exist
    returns the default value.
    """
    if entryname in dict_obj:
        result = dict_obj[entryname]
    else:
        result = default_value
    return result


def get_mime_type(file_path: str) -> str:
    """
    Get the MIME type for a given file extension.

    Args:
        file_path (str): file name, file path or extension only.

    Returns:
        str: The corresponding mimetype (e.g., 'image/jpeg', 'image/png').
    """
    file_path_to_guess_type = file_path
    extension = get_file_extension(file_path=file_path)
    if extension == '':
        # Assumes it's a extension-only, not a file name
        extension = file_path
        file_path_to_guess_type = f"dummy.{extension}"
    mime = MimeTypes()
    mime_type, _ = mime.guess_type(file_path_to_guess_type)
    if mime_type:
        return mime_type
    mime_types = {
        'wav': 'audio/x-wav',
        'mp3': 'audio/mpeg',
        'opus': 'audio/opus',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff',
        'svg': 'image/svg+xml',
    }
    return mime_types.get(extension.lower(), 'application/octet-stream')


def get_valid_extensions(extension_type: str = None) -> list:
    """
    Returns the list of valid extension for a given extension type.
    If the extension type is None, returns all valid extension.
    If the extension type is not valid, returns no valid extensions
    as an empty list.
    """
    valid_extensions = {
        "image": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg"],
        "json": ["json"],
        "text": ["txt", "md"],
        "csv": ["csv"],
        "audio": ["mp3", "wav", "flac"],
        "data_science": ["csv", "tsv", "parquet", "feather", "hdf5"],
        "other": ["docx", "pptx", "xlsx", "pdf"]
    }
    if extension_type:
        return valid_extensions.get(extension_type, [])
    flatten_list = []
    for list_element in valid_extensions.values():
        flatten_list += list_element
    return flatten_list


def get_url_query_args(url: str) -> dict:
    """
    Returns a dict with the key=value pairs in a URL query string
    """
    if len(url.split("?")) > 1:
        _, query_args_plain = url.split("?")
    else:
        query_args_plain = url
    query_args = query_args_plain.split("&")
    return {
        v.split("=")[0]: v.split("=")[1]
        if len(v.split("=")) > 1 else None
        for v in query_args
    }


def get_file_extension(file_path: str) -> str:
    """
    Returns the file extension from a path or filename.
    If there's no "." in file_path, assumes there's no file extension, so
    returns an empty string.
    """
    if file_path is None:
        return ''
    if len(file_path.split('.')) > 1:
        return file_path.split('.')[-1]
    return ''


def get_last_url_element(url: str) -> str:
    """
    Returns the last element from a URL (normally a file or page name)
    """
    return url.split('/')[-1]


def deduce_filename_from_url(url: str, extension_type: str = None) -> str:
    """
    Deduces a filename from a URL and checks if it has a valid extension.
    If not, tries to get a query parameter or REST API element that seems
    to be a filename.
    As a third attempt, uses regex to figure out a filename with a
    valid extension.
    """
    # First attempt: get the last element from the URL
    valid_extensions = get_valid_extensions(extension_type)
    filename = get_last_url_element(url)
    file_extension = get_file_extension(filename)
    if file_extension.lower() in valid_extensions:
        if DEBUG:
            log_debug(f"\n1st attempt: {filename}\n")
        return get_last_url_element(filename)
    # Second attempt: Check query parameters for a filename
    query_args = get_url_query_args(url)
    for key, value in query_args.items():
        if key.lower() in ['filename', 'file', 'name', 'f', 'n'] and \
           get_file_extension(value) in valid_extensions:
            if DEBUG:
                log_debug(f"\n2nd attempt [1]: {value} in key: {key}\n")
            return get_last_url_element(value)
    # for value in query_args.values():
    for key, value in query_args.items():
        if get_file_extension(value) in valid_extensions:
            if DEBUG:
                log_debug(f"\n2nd attempt [2]: {value} in key: {key}\n")
            return get_last_url_element(value)
    # Third attempt: Use regex to find a filename with a valid extension
    # e.g. on REST API elements
    pattern = r'/([^/?#]+)\.(' + '|'.join(valid_extensions) + ')(?=[?#]|$)'
    match = re.search(pattern, url)
    if match:
        value = match.group(1) + '.' + match.group(2)
        log_debug(f"\n3rd attempt: {value} | match: {match}\n")
        return get_last_url_element(value)
    if DEBUG:
        log_debug("\nNo way Jose\n")
    return ''


def interpret_any(any_input: Any) -> str:
    """
    Interpret the input and return a string representation.

    Args:
        any_input (Any): The input to interpret.

    Returns:
        str: A string representation of the interpreted input.
    """
    result = any_input
    if isinstance(any_input, dict):
        result = " ".join(list(any_input.values()))
    elif isinstance(any_input, list):
        result = " ".join(any_input)
    elif not isinstance(any_input, str):
        result = str(any_input)
    return result


def is_under_test() -> bool:
    """
    Returns True if the current environment is under test.
    """
    return 'PYTEST_CURRENT_TEST' in os.environ
