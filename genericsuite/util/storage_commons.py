from typing import Optional, Union
import os
from datetime import datetime

from genericsuite.config.config import Config
from genericsuite.util.encryption import encrypt_string, decrypt_string

settings = Config()

DEBUG = False

DEFAULT_PRESIGNED_EXPIRATION_SECONDS = 5*60
STORAGE_URL_SEPARATOR = '||'

STORAGE_ENCRYPTION = os.environ.get('STORAGE_ENCRYPTION', '')
STORAGE_PRESIGNED_EXPIRATION_SECONDS = os.environ.get(
    'STORAGE_PRESIGNED_EXPIRATION_SECONDS')
URL_MASK_EXTERNAL_PROTOCOL = os.environ.get('URL_MASK_EXTERNAL_PROTOCOL')
DEV_MASK_EXT_HOSTNAME = os.environ.get('DEV_MASK_EXT_HOSTNAME')
RUN_PROTOCOL = os.environ.get('RUN_PROTOCOL', 'https')


def get_dev_mask_ext_hostname() -> str:
    """
    Get the development external hostname.
    Returns:
        str: The development external hostname.
    """
    return DEV_MASK_EXT_HOSTNAME or ''


def get_storage_presigned_expiration_seconds(
    expiration_seconds: Union[int, str, None] = None
) -> int:
    """
    Get the storage presigned expiration seconds.
    Args:
        expiration_seconds (Union[int, str, None]): The expiration seconds.
    Returns:
        int: The storage presigned expiration seconds.
    """
    return int(
        expiration_seconds
        if expiration_seconds
        else STORAGE_PRESIGNED_EXPIRATION_SECONDS
        if STORAGE_PRESIGNED_EXPIRATION_SECONDS
        else DEFAULT_PRESIGNED_EXPIRATION_SECONDS
    )


def storage_encryption_enabled() -> bool:
    """
    Check if storage encryption is enabled.
    Returns:
        bool: True if storage encryption is enabled, False otherwise.
    """
    return STORAGE_ENCRYPTION == '1'


def get_storage_masked_url(
    bucket_name: str, key: str,
    hostname: Optional[Union[str, None]] = None
):
    """
    Get S3 bucket masked URL
    Args:
        bucket_name (str): The base path of the S3 bucket.
        key (str): The S3 key of the object to be retrieved.
    Returns:
        str: The S3 bucket masked URL
    """
    if hostname:
        # If hostname is provided, it's a development environment.
        # Use it instead of the default hostname
        protocol = URL_MASK_EXTERNAL_PROTOCOL or RUN_PROTOCOL
    else:
        hostname = settings.APP_HOST_NAME
        protocol = RUN_PROTOCOL
    extension = key.split('.')[-1] if '.' in key else ''
    extension = '.' + extension if extension else ''
    key = key.rsplit('.', 1)[0] if '.' in key else key
    return protocol + '://' + hostname + "/assets/" + \
        encrypt_string(
            settings.STORAGE_URL_SEED,
            bucket_name + STORAGE_URL_SEPARATOR + key
        ) + \
        extension


def get_decripted_item_id(raw_item_id: str) -> str:
    """
    Get the decrypted item ID from the raw item ID.
    Args:
        raw_item_id (str): The raw item ID.
    Returns:
        str: The decrypted item ID.
    """
    decripted_item_id = decrypt_string(settings.STORAGE_URL_SEED, raw_item_id)
    if not decripted_item_id:
        raise Exception("Invalid asset")
    return decripted_item_id


def get_bucket_key_from_decripted_item_id(raw_item_id: str) -> tuple[str, str]:
    """
    Get the bucket name and file path from the decrypted item ID.
    Args:
        raw_item_id (str): The raw item ID.
    Returns:
        tuple[str, str]: The bucket name and file path.
    """
    decripted_item_id = get_decripted_item_id(raw_item_id)
    bucket_name, key = decripted_item_id.split(STORAGE_URL_SEPARATOR)
    return bucket_name, key


def get_nodup_filename(file_name: str) -> str:
    """
    Generate a unique filename to prevent overwriting existing files.
    Appends the current date and time to the original file name, ensuring that
    the uploaded file does not duplicate an existing file.
    Also replaces blanks with "_".

    Args:
        file_name (str): The original file name.

    Returns:
        str: A unique filename with the current date and time appended.
    """
    result = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}" + \
        f"_{file_name}"
    result = result.replace(" ", "_")
    result = result.replace(" ", "_")
    return result
