from typing import Optional, Union, Any
from genericsuite.util.utilities import (
    error_resultset,
)
from genericsuite.util.framework_abs_layer import Request


def remove_from_storage(bucket_name: str, key: str) -> dict:
    """
    Remove an object from a GCP storage bucket.

    Args:
        bucket_name (str): The base path of the GCP storage bucket.
        key (str): The GCP storage bucket key of the object to be removed.
    """
    return error_resultset("Not implemented")


def gcp_storage_base_url(bucket_name: str) -> str:
    """
    Returns the GCP storage base URL.

    Args:
        bucket_name (str): The base path of the GCP storage bucket.

    Returns:
        str: The GCP storage base URL.
    """
    return f"https://{bucket_name}.storage.googleapis.com"


def upload_file_to_storage(
    bucket_name: str,
    source_path: str,
    dest_path: str,
    public_file: bool = False
) -> dict:
    """
    Uploads a local file to an GCP bucket.

    Args:
        bucket_name (str): The base path of the GCP bucket.
        source_path (str): The local path of the file.
        dest_path (str): The GCP bucket path of the file.
        public_file (bool): True to make the file public (ACL public-read)

    Returns:
        dict: a Dict with the following elements:
            public_url (str): The GCP bucket (or encrypted) URL of the
                uploaded file.
            final_filename (str): the final filename (with a date/time prefix)
            error (bool): True if there was any error.
            error_message (str): The eventual error message
    """
    return error_resultset("Not implemented")


def storage_retieval(
    request: Request,
    blueprint: Any,
    item_id: Union[str, None],
    other_params: Optional[dict] = None,
) -> dict:
    """
    Get GCP bucket content from encrypted item_id
    Args:
        request (Request): the request object.
        blueprint (Any): the blueprint object,
        other_params (dict, optional): Other parameters. Defaults to None.
        item_id (str, optional): The item_id with the encrypted elements
            (bucket_name, separator and key). Defaults to None.
    Returns:
        dict: The object as a standard resultset dictionary,
            with the file content in the 'content' element,
            the mime type in the 'mime_type' element,
            the file name in the 'filename' element (GCP bucket key),
            the downloaded local file path in 'local_file_path' element,
            or error/error_message elements.
    """
    return error_resultset("Not implemented")


def prepare_asset_url(public_url: str) -> str:
    """
    Prepares the asset (image, sound, file) URL for the GPT4 vision message
    content. If DEV_MASK_EXT_HOSTNAME is set, it will be prepended to the URL.
    Args:
        public_url (str): The public URL of the image.
    Returns:
        str: The prepared image URL.
    """
    raise Exception("Not implemented")
