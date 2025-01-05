"""
This module contains utility functions for working with files.
"""
from typing import Optional
import os
from uuid import uuid4

from genericsuite.config.config import Config


def temp_filename(extension: Optional[str] = None) -> str:
    """
    Returns a temporary filename with the specified extension.

    Args:
    extension (str): The extension of the temporary file.
    If None, the extension is randomly generated.

    Returns
    str: The temporary path/filename.
    """
    return os.path.join(temp_dir(), secure_filename(extension))


def temp_dir() -> str:
    """
    Returns the path to a temporary directory.

    Returns
    str: The path to the temporary directory.
    """
    settings = Config()
    return settings.TEMP_DIR


def secure_filename(extension: Optional[str] = None) -> str:
    """
    Returns a secure filename.

    Args:
    extension (str): The extension of the file.

    Returns
    str: The secure filename.
    """
    if extension is None:
        filename = f"{uuid4().hex}"
    else:
        filename = f"{uuid4().hex}.{extension}"
    return filename
