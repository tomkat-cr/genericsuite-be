"""
The parse_multipart module handles the multipart form-data parsing,
and get content like upoaded files.
"""
import os

from requests_toolbelt import MultipartDecoder

from genericsuite.util.app_logger import log_debug
from genericsuite.util.utilities import return_resultset_jsonified_or_exception
from genericsuite.util.app_context import AppContext
from genericsuite.util.file_utilities import temp_filename

DEBUG = False


def parse_multipart(raw_body, headers):
    """
    The parse_multipart function is implemented to handle the multipart
    form data parsing, and get content like upoaded files.
    (solves "multipart/form-data" and Chalice nightmare!)
    """
    content_type = headers['content-type']
    if content_type == 'multipart/form-data':
        content_type += "; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"
    decoder = MultipartDecoder(raw_body, content_type)

    # It returns the list of parts, but only content and encoding.
    # For files, he "name" (and "file_name") weont be passed.

    def get_part(part):
        disposition = part.headers.get(b'Content-Disposition', "")
        params = {}
        for disp_part in str(disposition).split(';'):
            kv = disp_part.split('=', 2)
            params[str(kv[0]).strip()] = (
                str(kv[1]).strip('\"\'\t \r\n')
                if len(kv) > 1 else str(kv[0]).strip()
            )
        part_type = (
            part.headers[b'Content-Type']
            if b'Content-Type' in part.headers else None
        )
        return {
            "content": part.content,
            "type": part_type,
            "params": params,
            "headers": part.headers,
            "encoding": part.encoding,
        }

    # parsed_parts = {"parts": [p.content for p in decoder.parts]}
    parsed_parts = {
        "parts": [get_part(p) for p in decoder.parts]
    }
    if DEBUG:
        log_debug("")
        log_debug(f">>--> PARSE_MULTIPART | parsed_parts: {parsed_parts}")
        log_debug("")
    return parsed_parts


def file_upload_handler(app_context: AppContext, p: dict):
    """
    Handle the file upload process.

    This function takes a dictionary with 'extension' and 'handler_function',
    saves the uploaded file to a temporary directory, processes it using the
    specified handler function, and then cleans up by removing the temporary
    file.

    :param p: A dictionary containing 'extension' and 'handler_function'.
    :return: The result of the handler function or an error message.
    """
    request = app_context.get_request()
    if "other_params" not in p:
        p["other_params"] = {}

    if "uploaded_file_path" in p and p.get("uploaded_file_path"):
        # File was already uploaded (e.g. FastAPI)
        if p['uploaded_file_path']:
            file_path = p['uploaded_file_path']
        else:
            return return_resultset_jsonified_or_exception({
                'error': True,
                'error_message': 'No file provided [1]'
            })
    else:
        # Ensure the request content type is multipart/form-data (e.g. Chalice)
        if request.headers['Content-Type'].startswith('multipart/form-data'):
            parsed_body = parse_multipart(request.raw_body, request.headers)

            if parsed_body['parts'][0]["content"]:
                file_path = download_file(
                    parsed_body['parts'][0]["content"],
                    p['extension'],
                )
            else:
                return return_resultset_jsonified_or_exception({
                    'error': True,
                    'error_message': 'No file provided [2]'
                })
        else:
            return return_resultset_jsonified_or_exception({
                'error': True,
                'error_message': 'Unsupported media type, expected' +
                ' multipart/form-data'
            })

    # Pass additional parameters from the 'other_params' dict to
    # the handler function
    param_name = p.get("file_path_param_name", "file_path")
    if "unique_param_name" in p:
        p["other_params"][p["unique_param_name"]][param_name] = \
            file_path
    else:
        p["other_params"][param_name] = file_path

    # Call the handler function
    log_debug('Call the handler function:\n' +
                f'{p["handler_function"]}({p["other_params"]})')

    result = p["handler_function"](
        **p["other_params"]
    )
    if p.get("delete_file_after_processing", True):
        if DEBUG:
            log_debug(f">> Cleaning up: {file_path}...")
        os.remove(file_path)  # Clean up the temporary file
    else:
        log_debug(f">> File left in device: {file_path}")
    return return_resultset_jsonified_or_exception(result)


def download_file(file_data: bytes, extension: str) -> str:
    """
    Download the file data to a temporary directory.

    :param file_data: The file data to download.
    :return: The path to the downloaded file.
    """
    file_path = temp_filename(extension)
    with open(file_path, 'wb') as file:
        file.write(file_data)
    return file_path
