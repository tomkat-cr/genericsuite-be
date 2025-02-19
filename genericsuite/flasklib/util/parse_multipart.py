"""
FastAPI parse multipart module to handle downloaded files.

Reference:
https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
"""
import os
from flask import request

from genericsuite.util.utilities import (
    get_file_extension,
    get_default_resultset,
    error_resultset,
)
from genericsuite.util.file_utilities import temp_dir, secure_filename


def download_file_flask() -> str:
    """
    Downloads a file from a FastAPI UploadFile object.
    Returns:
        str: the path to the downloaded file.
    """
    if request.method != 'POST':
        return error_resultset(
            error_message="Method is not POST",
            message_code="PM-DFF-E100")

    # Check if the post request has the file part
    if 'file' not in request.files:
        return error_resultset(
            error_message="No file part",
            message_code="PM-DFF-E200",
        )
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return error_resultset(
            error_message="No selected file",
            message_code="PM-DFF-E300",
        )
    if file:
        extension = get_file_extension(file.filename)
        file_path = os.path.join(temp_dir(), secure_filename(extension))
        file.save(file_path)
        result = get_default_resultset()
        result['file_path'] = file_path
        return result
    return error_resultset(
        error_message="No file provided",
        message_code="PM-DFF-E300",
    )
