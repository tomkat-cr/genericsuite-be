"""
FastAPI parse multipart module to handle downloaded files.
"""
from typing import Optional

from fastapi import UploadFile

from genericsuite.util.utilities import get_file_extension
from genericsuite.util.parse_multipart import download_file


async def download_file_fa(
    file: UploadFile,
    extension: Optional[str] = None
) -> str:
    """
    Downloads a file from a FastAPI UploadFile object.
    Args:
        file (UploadFile): the file to download.
    Returns:
        str: the path to the downloaded file.
    """
    if extension is None:
        extension = get_file_extension(file.filename)
    contents = await file.read()
    uploaded_file_path = download_file(file_data=contents, extension=extension)
    contents = None
    return uploaded_file_path
