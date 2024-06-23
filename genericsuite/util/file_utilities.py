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
    settings = Config()
    if extension is None:
        filename = f"{uuid4().hex}"
    else:
        filename = f"{uuid4().hex}.{extension}"
    file_path = os.path.join(settings.TEMP_DIR, filename)
    return file_path
