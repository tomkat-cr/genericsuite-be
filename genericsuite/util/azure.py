from typing import Optional, Union, Any
from genericsuite.util.utilities import (
    error_resultset,
)
from genericsuite.util.framework_abs_layer import Request


def remove_from_storage(bucket_name: str, key: str) -> dict:
    """
    Remove an object from an Azure blob storage.

    Args:
        bucket_name (str): The base path of the Azure blob storage.
        key (str): The Azure blob storage key of the object to be removed.
    """
    return error_resultset("Not implemented")


def blob_storage_base_url(bucket_name: str) -> str:
    """
    Returns the Azure blob storage base URL.

    Args:
        bucket_name (str): The base path of the Azure blob storage.

    Returns:
        str: The Azure blob storage base URL.
    """
    return f"https://{bucket_name}.blob.core.windows.net"


def upload_file_to_storage(
    bucket_name: str,
    source_path: str,
    dest_path: str,
    public_file: bool = False
) -> dict:
    """
    Uploads a local file to an Azure blob storage.

    Args:
        bucket_name (str): The base path of the Azure blob storage.
        source_path (str): The local path of the file.
        dest_path (str): The Azure blob storage path of the file.
        public_file (bool): True to make the file public (ACL public-read)

    Returns:
        dict: a Dict with the following elements:
            public_url (str): The Azure blob storage (or encrypted) URL of the
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
    Get Azure blob storage content from encrypted item_id
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
            the file name in the 'filename' element (Azure blob storage key),
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
