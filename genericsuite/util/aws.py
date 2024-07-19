"""
AWS Utilities
"""
from typing import Optional, Union, Any
from datetime import datetime
import os
import json
from urllib.parse import urlparse

import requests

import boto3
from botocore.exceptions import NoCredentialsError

from genericsuite.config.config_from_db import app_context_and_set_env
from genericsuite.util.framework_abs_layer import Request
from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.utilities import (
    get_default_resultset,
    error_resultset,
    get_mime_type,
    get_file_extension,
)
from genericsuite.util.encryption import decrypt_string, encrypt_string
from genericsuite.util.file_utilities import temp_filename
from genericsuite.config.config import Config

DEBUG = True

STORAGE_URL_SEPARATOR = '||'
STORAGE_ENCRYPTION = os.environ.get('STORAGE_ENCRYPTION', '') == '1'


def s3_base_url(bucket_name: str) -> str:
    """
    Returns the S3 base URL.

    Args:
        bucket_name (str): The base path of the S3 bucket.

    Returns:
        str: The S3 base URL.
    """
    return f"https://{bucket_name}.s3.amazonaws.com"


def upload_nodup_file_to_s3(
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

    # If the original filename is specified, uses it, if not
    # use the local path's file name
    if original_filename:
        final_filename = original_filename
    else:
        final_filename = os.path.basename(file_path)

    # Add date/time to avoid file name duplicates
    final_filename = s3_nodup_filename(final_filename)

    # Construct the S3 bucket path
    dest_path = (f"{sub_dir}/" if sub_dir else "") + final_filename

    return upload_file_to_s3(
        bucket_name=bucket_name,
        source_path=file_path,
        dest_path=dest_path,
        public_file=public_file,
    )


def upload_file_to_s3(
    bucket_name: str,
    source_path: str,
    dest_path: str,
    public_file: bool = False
) -> dict:
    """
    Uploads a local file to an S3 bucket.

    Args:
        bucket_name (str): The base path of the S3 bucket.
        source_path (str): The local path of the file.
        dest_path (str): The S3 path of the file.
        public_file (bool): True to make the file public (ACL public-read)

    Returns:
        dict: a Dict with the following elements:
            public_url (str): The S3 (or encrypted) URL of the uploaded file.
            final_filename (str): the final filename (with a date/time prefix)
            error (bool): True if there was any error.
            error_message (str): The eventual error message
    """
    error = None
    result = get_default_resultset()

    # Initialize S3 client
    s3_client = boto3.client('s3')

    try:
        # Upload the file
        s3_client.upload_file(
            source_path,
            bucket_name,
            dest_path,
        )
        log_debug(f"\nFile uploaded successfully S3 Bucket: {bucket_name}" +
                  f" | path: {dest_path}")
    except FileNotFoundError:
        error = f"The file {source_path} was not found."
        log_debug(error)
    except NoCredentialsError:
        error = "Credentials not available for S3 upload."
        log_debug(error)

    if public_file and not error:
        try:
            # Enable public access for the uploaded file
            # It seems that setting the ACL to 'public-read'
            # is not turning the object public...
            # As an alternative, we can use the put_bucket_policy method
            # to make the bucket public
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AddPerm",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/{dest_path}"
                    }
                ]
            }
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(policy)
            )
            log_debug(f"Bucket policy for '{dest_path}' set to public-read" +
                      " successfully")
        # except s3_client.exceptions.S3Error as e:
        except Exception as err:
            error = f"Failed to set ACL for {dest_path}: {err}"
            log_debug(error)

    if STORAGE_ENCRYPTION:
        # Return the encrypted S3 URL of the uploaded file
        public_url = get_storage_masked_url(bucket_name, dest_path)
    else:
        # Return the public S3 URL of the uploaded file
        public_url = f"{s3_base_url(bucket_name)}/{dest_path}"

    # Final filanme is the file name in the S3 destination path.
    final_filename = os.path.basename(dest_path)

    log_debug(f"Public url: {public_url}")
    log_debug(f"Final filename: {final_filename}")
    log_debug(f"Error: {error}\n")

    result['public_url'] = public_url
    result['final_filename'] = final_filename
    result['error'] = error is not None
    result['error_message'] = error
    return result
    # return public_url, final_filename, error


def s3_nodup_filename(file_name):
    """
    Generate a unique filename for S3 to prevent overwriting existing files.

    Appends the current date and time to the original file name, ensuring that
    the uploaded file does not duplicate an existing file in the S3 bucket.
    Also replaces blanks with "_".

    Parameters:
        file_name (str): The original file name.

    Returns:
        str: A unique S3 filename with the current date and time appended.
    """
    result = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}" + \
             f"_{file_name}"
    result = result.replace(" ", "_")
    result = result.replace(" ", "_")
    return result


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
    settings = Config()
    result = get_default_resultset()
    if not original_filename:
        original_filename = url.split('/')[-1]
    response = requests.get(url, timeout=10)    # 10 seconds timeout
    tmp_file_path = settings.TEMP_DIR + '/' + original_filename
    with open(tmp_file_path, 'wb') as f_handler:
        f_handler.write(response.content)
    # file_size = os.stat(tmp_file_path).st_size
    result['file_size'] = os.stat(tmp_file_path).st_size
    # public_url, final_filename, error = upload_nodup_file_to_s3(
    upload_result = upload_nodup_file_to_s3(
        file_path=tmp_file_path,
        original_filename=original_filename,
        bucket_name=bucket_name,
        sub_dir=sub_dir,
    )
    # attachment_url = public_url
    os.remove(tmp_file_path)  # Clean up the temporary file

    result['public_url'] = upload_result['public_url']
    result['final_filename'] = upload_result['final_filename']
    result['error'] = upload_result['error']
    result['error_message'] = upload_result['error_message']
    return result
    # return attachment_url, final_filename, file_size, error


def remove_from_s3(bucket_name: str, key: str) -> dict:
    """
    Remove an object from an S3 bucket.

    Args:
        bucket_name (str): The base path of the S3 bucket.
        key (str): The S3 key of the object to be removed.
    """
    result = get_default_resultset()
    try:
        s3 = boto3.client('s3')
        s3.delete_object(Bucket=bucket_name, Key=key)
        log_debug(f"Object removed from S3: {bucket_name}/{key}")
    except Exception as err:
        result['error'] = True
        result['error_message'] = f"Failed to remove object from S3: {err}"
        log_debug(result['error_message'])
    return result


def get_s3_object(bucket_name: str, key: str) -> dict:
    """
    Get an object from an S3 bucket.

    Args:
        bucket_name (str): The base path of the S3 bucket.
        key (str): The S3 key of the object to be retrieved.

    Returns:
        dict: The object as a standard resultset dictionary,
            with the file content in the 'content' element
            or error/error_message elements.
    """
    result = get_default_resultset()
    try:
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket_name, Key=key)
        # result['content'] = obj['Body'].read().decode('utf-8')
        result['content'] = obj['Body'].read()
        log_debug(f"Object retrieved from S3: {bucket_name}/{key}")
    except Exception as err:
        result['error'] = True
        result['error_message'] = f"Failed to retrieve object from S3: {err}"
        log_error(result['error_message'])
    return result


def download_s3_object(bucket_name: str, key: str,
                       local_file_path: Optional[str] = None) -> dict:
    """
    Download an object from an S3 bucket in a temporary path.

    Args:
        bucket_name (str): The base path of the S3 bucket.
        key (str): The S3 key of the object to be retrieved.
        local_file_path (str, optional): The temporary path to download
            the file.
            If None, it will use a random-generated temporary path.
            Defaults to None.

    Returns:
        dict: The object as a standard resultset dictionary,
            with the file temp_path/filename in the 'local_file_path' element
            or error/error_message elements.
    """
    result = get_default_resultset()
    if not local_file_path:
        local_file_path = temp_filename(get_file_extension(file_path=key))
    try:
        s3_client = boto3.client('s3')
        s3_client.download_file(bucket_name, key, local_file_path)
        result['local_file_path'] = local_file_path
        log_debug(f"Object downloaded from S3: {bucket_name}/{key}")
    except Exception as err:
        result['error'] = True
        result['error_message'] = \
            f"ERROR-DS3O-010 - Failed to download object: {err}"
        log_error(result['error_message'])
    return result


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
    settings = Config()
    if hostname:
        # If hostname is provided, it's a development environment.
        # Use it instead of the default hostname
        protocol = os.environ.get('URL_MASK_EXTERNAL_PROTOCOL')
        protocol = protocol or os.environ.get('RUN_PROTOCOL', 'https')
    else:
        hostname = settings.APP_HOST_NAME
        protocol = 'https'
    extension = key.split('.')[-1] if '.' in key else ''
    extension = '.' + extension if extension else ''
    key = key.rsplit('.', 1)[0] if '.' in key else key
    return protocol + '://' + hostname + "/asset/" + \
        encrypt_string(
            settings.STORAGE_URL_SEED,
            bucket_name + STORAGE_URL_SEPARATOR + key
        ) + \
        extension


def storage_retieval(
    request: Request,
    blueprint: Any,
    item_id: Union[str, None],
    other_params: Optional[dict] = None,
) -> dict:
    """
    Get S3 bucket content from encrypted item_id
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
            the file name in the 'filename' element (S3 key),
            the downloaded local file path in 'local_file_path' element,
            or error/error_message elements.
    """
    if other_params is None:
        other_params = {}
    if not other_params.get('mode'):
        # Default mode is 'get', the other option is 'download'
        other_params['mode'] = 'get'
    # Set environment variables from the database configurations.
    app_context = app_context_and_set_env(request=request, blueprint=blueprint)
    if app_context.has_error():
        return app_context.get_error_resultset()
    settings = Config(app_context)
    if not item_id:
        return error_resultset("Item ID is required", "ASR-E1010")
    # Decrypt item_id to get the bucket_name and key (filespec)
    extension = item_id.split('.')[-1] if '.' in item_id else ''
    extension = '.' + extension if extension else ''
    raw_item_id = item_id.rsplit('.', 1)[0] if '.' in item_id else item_id
    decripted_item_id = decrypt_string(settings.STORAGE_URL_SEED, raw_item_id)
    if not decripted_item_id:
        return error_resultset("Invalid asset", "ASR-E1020")
    # Get bucket name and file path
    bucket_name, key = decripted_item_id.split(STORAGE_URL_SEPARATOR)
    key = key+extension
    # Get the file content
    if DEBUG:
        log_debug(f">> bucket_name: {bucket_name} | key: {key}")
    if other_params['mode'] == 'get':
        retrieval_resultset = get_s3_object(bucket_name=bucket_name, key=key)
    else:
        retrieval_resultset = download_s3_object(bucket_name=bucket_name,
                                                 key=key)
    if retrieval_resultset.get('error'):
        # return retrieval_resultset
        return error_resultset(retrieval_resultset['error_message'],
                               "ASR-E1030")
    retrieval_resultset['mime_type'] = get_mime_type(key)
    retrieval_resultset['filename'] = key
    return retrieval_resultset


def prepare_asset_url(public_url):
    """
    Prepares the asset (image, sound, file) URL for the GPT4 vision message
    content. If DEV_MASK_EXT_HOSTNAME is set, it will be prepended to the URL.
    Args:
        public_url (str): The public URL of the image.
    Returns:
        str: The prepared image URL.
    """
    dev_mask_ext_hostname = os.environ.get('DEV_MASK_EXT_HOSTNAME')
    final_public_url = public_url
    if dev_mask_ext_hostname and STORAGE_ENCRYPTION:
        parsed_url = urlparse(public_url)
        final_public_url = dev_mask_ext_hostname + parsed_url.path
        if DEBUG:
            log_debug("prepare_asset_url" +
                      f" | dev_mask_ext_hostname: {dev_mask_ext_hostname}"
                      f" | parsed_url: {parsed_url}"
                      f" | final_public_url: {final_public_url}")
    return final_public_url
