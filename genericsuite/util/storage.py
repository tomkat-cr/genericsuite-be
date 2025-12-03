from typing import Optional, Union, Any, Callable
from urllib.parse import urlparse
import requests
import os

from genericsuite.config.config import Config
from genericsuite.util.framework_abs_layer import Request
from genericsuite.util.utilities import error_resultset, get_default_resultset
from genericsuite.util.app_logger import log_debug
from genericsuite.util.cloud_provider_abstractor import get_cloud_provider

from genericsuite.util.storage_commons import (
    storage_encryption_enabled,
    get_dev_mask_ext_hostname,
    get_nodup_filename,
)

from genericsuite.util.aws import (
    storage_retieval as aws_storage_retieval,
    prepare_asset_url as aws_prepare_asset_url,
    upload_file_to_s3 as aws_upload_file_to_storage,
    remove_from_s3 as aws_remove_from_storage,
    s3_base_url as aws_storage_base_url,
)
from genericsuite.util.azure import (
    storage_retieval as azure_storage_retieval,
    prepare_asset_url as azure_prepare_asset_url,
    upload_file_to_storage as azure_upload_file_to_storage,
    remove_from_storage as azure_remove_from_storage,
    blob_storage_base_url as azure_storage_base_url,
)
from genericsuite.util.gcp import (
    storage_retieval as gcp_storage_retieval,
    prepare_asset_url as gcp_prepare_asset_url,
    upload_file_to_storage as gcp_upload_file_to_storage,
    remove_from_storage as gcp_remove_from_storage,
    gcp_storage_base_url as gcp_storage_base_url,
)

DEBUG = False


def remove_from_storage(bucket_name: str, key: str) -> dict:
    """
    Remove an object from a storage bucket.

    Args:
        bucket_name (str): The base path of the S3 bucket.
        key (str): The S3 key of the object to be removed.
    """
    try:
        cloud_provider = get_cloud_provider()
    except Exception as e:
        return error_resultset(str(e))
    if cloud_provider == "AWS":
        caller_function = aws_remove_from_storage
    elif cloud_provider == "AZURE":
        caller_function = azure_remove_from_storage
    elif cloud_provider == "GCP":
        caller_function = gcp_remove_from_storage
    return caller_function(bucket_name, key)


def get_storage_base_url(bucket_name: str) -> str:
    """
    Returns the storage base URL.

    Args:
        bucket_name (str): The base path of the storage bucket.

    Returns:
        str: The storage base URL.
    """
    try:
        cloud_provider = get_cloud_provider()
    except Exception as e:
        return error_resultset(str(e))
    if cloud_provider == "AWS":
        return aws_storage_base_url(bucket_name)
    elif cloud_provider == "AZURE":
        return azure_storage_base_url(bucket_name)
    elif cloud_provider == "GCP":
        return gcp_storage_base_url(bucket_name)


def get_upload_file_to_storage_caller(cloud_provider: str) -> Callable:
    """
    This function is used to get the appropriate upload file to storage caller
    function for the given cloud provider.
    Args:
        cloud_provider (str): The cloud provider.
    Returns:
        Callable: The upload file to storage caller function.
    """
    if cloud_provider == "AWS":
        return aws_upload_file_to_storage
    elif cloud_provider == "AZURE":
        return azure_upload_file_to_storage
    elif cloud_provider == "GCP":
        return gcp_upload_file_to_storage
    else:
        raise Exception(f"Cloud provider '{cloud_provider}' not supported"
                        " [ST-GUFSC-E010]")


def upload_nodup_file_to_storage(
    file_path: str,
    original_filename: str,
    bucket_name: str,
    sub_dir: Optional[Union[str, None]] = None,
    public_file: bool = False,
) -> dict:
    """
    Uploads a local file to an S3 bucket.

    Args:
        file_path (str): The local path of the file.
        original_filename (str): If the original filename is specified,
        uses it, if not use the local path's file name.
        bucket_name (str): The base path of the S3 bucket.
        sub_dir (str): intermediate path. Defaults to None.
        public_file (bool): True to make the file public.

    Returns:
        str: The S3 URL of the uploaded file.
        str: the final filename (with a date/time prefix)
        str: The eventual error message
    """
    try:
        cloud_provider = get_cloud_provider()
    except Exception as e:
        return error_resultset(str(e))

    # If the original filename is specified, uses it, if not
    # use the local path's file name
    if original_filename:
        final_filename = original_filename
    else:
        final_filename = os.path.basename(file_path)

    # Add date/time to avoid file name duplicates
    final_filename = get_nodup_filename(final_filename)

    # Construct the S3 bucket path
    dest_path = (f"{sub_dir}/" if sub_dir else "") + final_filename

    caller_function = get_upload_file_to_storage_caller(cloud_provider)
    return caller_function(
        bucket_name=bucket_name,
        source_path=file_path,
        dest_path=dest_path,
        public_file=public_file,
    )


def save_file_from_url(
    url: str,
    bucket_name: str,
    sub_dir: Optional[str] = None,
    original_filename: Optional[str] = None
) -> dict:
    """
    Save an image from a URL to AWS S3

    Args:
        url (str): The URL to get the image.
        bucket_name (str): The base path of the S3 bucket.
        sub_dir (str): intermediate path. Defaults to None.
        original_filename (str): original file name. Defaults to None.
        If original_filename is None, it will be the last element
        of the URL split by "/".

    Returns:
        (str, str, int, str): a tuple with the following elements:
        public_url (str): URL for the image.
        final_filename (str): file name of the image with date/time added.
        file_size (int): the file size in bytes.
        error (str): the eventual error message or None if no errors
    """
    try:
        cloud_provider = get_cloud_provider()
    except Exception as e:
        return error_resultset(str(e))

    settings = Config()
    result = get_default_resultset()

    if not original_filename:
        original_filename = url.split('/')[-1]

    response = requests.get(url, timeout=10)    # 10 seconds timeout
    tmp_file_path = settings.TEMP_DIR + '/' + original_filename
    with open(tmp_file_path, 'wb') as f_handler:
        f_handler.write(response.content)

    result['file_size'] = os.stat(tmp_file_path).st_size

    caller_function = get_upload_file_to_storage_caller(cloud_provider)
    upload_result = caller_function(
        file_path=tmp_file_path,
        original_filename=original_filename,
        bucket_name=bucket_name,
        sub_dir=sub_dir,
    )

    # Clean up the temporary file
    os.remove(tmp_file_path)

    result['public_url'] = upload_result['public_url']
    result['final_filename'] = upload_result['final_filename']
    result['error'] = upload_result['error']
    result['error_message'] = upload_result['error_message']
    return result


def upload_file_to_storage(
    bucket_name: str,
    source_path: str,
    dest_path: str,
    public_file: bool = False,
) -> dict:
    """
    Uploads a local file to an S3/Azure/GCP bucket.

    Args:
        bucket_name (str): The base path of the S3/Azure/GCP bucket.
        source_path (str): The local path of the file.
        dest_path (str): The S3/Azure/GCP path of the file.
        public_file (bool): True to make the file public (ACL public-read)

    Returns:
        dict: a Dict with the following elements:
            public_url (str): The S3/Azure/GCP (or encrypted) URL of the
                uploaded file.
            final_filename (str): the final filename (with a date/time prefix)
            error (bool): True if there was any error.
            error_message (str): The eventual error message
    """
    try:
        cloud_provider = get_cloud_provider()
    except Exception as e:
        return error_resultset(str(e))

    if cloud_provider == "AWS":
        caller_function = aws_upload_file_to_storage
    elif cloud_provider == "AZURE":
        caller_function = azure_upload_file_to_storage
    elif cloud_provider == "GCP":
        caller_function = gcp_upload_file_to_storage

    return caller_function(bucket_name, source_path, dest_path, public_file)


def storage_retieval(
    request: Request,
    blueprint: Any,
    item_id: Union[str, None],
    other_params: Optional[dict] = None,
) -> dict:
    """
    Get S3/Azure/GCP storage content from encrypted item_id
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
            the file name in the 'filename' element (S3/Azure/GCP storage key),
            the downloaded local file path in 'local_file_path' element,
            or error/error_message elements.
    """
    try:
        cloud_provider = get_cloud_provider()
    except Exception as e:
        return error_resultset(str(e))

    # TODO: if this is not needed, remove the request and blueprint parameters
    # Set environment variables from the database configurations.
    # app_context = app_context_and_set_env(
    #   request=request, blueprint=blueprint)
    # if app_context.has_error():
    #     return app_context.get_error_resultset()
    # settings = Config(app_context)

    if cloud_provider == "AWS":
        caller_function = aws_storage_retieval
    elif cloud_provider == "AZURE":
        caller_function = azure_storage_retieval
    elif cloud_provider == "GCP":
        caller_function = gcp_storage_retieval

    return caller_function(item_id, other_params)


def prepare_asset_url(public_url: str) -> str:
    """
    Prepares the asset URL (image, sound, file) for message content for tools
    like GPT4 vision.
    If the storage encryption is enabled and DEV_MASK_EXT_HOSTNAME is set,
    the URL will be prepended with DEV_MASK_EXT_HOSTNAME. otherwise, the URL
    will be masked with a presigned method.
    Args:
        public_url (str): The public URL of the image. E.g.:
            https://<bucket-name>.s3.amazonaws.com/<user-id>/<file-name.jpg|png>

    Returns:
        str: The prepared image URL.
    """
    final_public_url = public_url

    if storage_encryption_enabled():
        parsed_url = urlparse(public_url)
        dev_mask_ext_hostname = get_dev_mask_ext_hostname()
        final_public_url = dev_mask_ext_hostname + parsed_url.path
        _ = DEBUG and log_debug(
            "prepare_asset_url" +
            f" | dev_mask_ext_hostname: {dev_mask_ext_hostname}"
            f" | parsed_url: {parsed_url}"
            f" | final_public_url: {final_public_url}"
        )
    else:
        try:
            cloud_provider = get_cloud_provider()
        except Exception as e:
            raise Exception(str(e))

        if cloud_provider == "AWS":
            caller_function = aws_prepare_asset_url
        elif cloud_provider == "AZURE":
            caller_function = azure_prepare_asset_url
        elif cloud_provider == "GCP":
            caller_function = gcp_prepare_asset_url

        final_public_url = caller_function(public_url)
        _ = DEBUG and log_debug(
            "prepare_asset_url" + f" | cloud_provider: {cloud_provider}"
            f" | public_url: {public_url}"
            f" | final_public_url: {final_public_url}"
        )
    return final_public_url
