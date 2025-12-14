"""
AWS Utilities
"""
from typing import Optional, Union
import os
import json
from urllib.parse import urlparse, unquote

from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.utilities import (
    get_default_resultset,
    error_resultset,
    get_mime_type,
    get_file_extension,
)
from genericsuite.util.file_utilities import temp_filename
from genericsuite.util.storage_commons import (
    get_storage_masked_url,
    get_bucket_key_from_decripted_item_id,
    storage_url_encryption_enabled,
    get_storage_presigned_expiration_seconds,
)


DEBUG = os.environ.get('CLOUD_AWS_DEBUG', '0') == '1'


def s3_base_url(bucket_name: str) -> str:
    """
    Returns the S3 base URL.

    Args:
        bucket_name (str): The base path of the S3 bucket.

    Returns:
        str: The S3 base URL.
    """
    return f"https://{bucket_name}.s3.amazonaws.com"


def get_bucket_key_from_url(public_url):
    """
    Get the S3 bucket name and key from the public URL.
    Args:
        public_url (str): The public URL of the image.
    Returns:
        tuple: The bucket name and key.
    """
    parsed_url = urlparse(public_url)
    bucket_name = parsed_url.hostname \
        .replace("https://", "") \
        .replace(".s3.amazonaws.com", "")
    # To avoid "/key"
    key = parsed_url.path[1:]
    return bucket_name, key


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
    import boto3
    from botocore.exceptions import NoCredentialsError

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
        _ = DEBUG and log_debug(
            "upload_file_to_s3" +
            f"\n | File uploaded successfully S3 Bucket: {bucket_name}" +
            f"\n | path: {dest_path}")
    except FileNotFoundError:
        error = f"The file {source_path} was not found."
        log_error(error)
    except NoCredentialsError:
        error = "Credentials not available for S3 upload."
        log_error(error)

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
            _ = DEBUG and log_debug(
                "upload_file_to_s3" +
                f"\n | Bucket policy for '{dest_path}' set to public-read" +
                " successfully")
        # except s3_client.exceptions.S3Error as e:
        except Exception as err:  # pylint: disable=broad-except
            error = f"Failed to set ACL for {dest_path}: {err}"
            log_debug(error)

    if storage_url_encryption_enabled():
        # Return the encrypted S3 URL of the uploaded file
        public_url = get_storage_masked_url(s3_client, bucket_name, dest_path)
    else:
        # Return the public S3 URL of the uploaded file
        public_url = f"{s3_base_url(bucket_name)}/{dest_path}"

    # Final filename is the file name in the S3 destination path.
    final_filename = os.path.basename(dest_path)

    _ = DEBUG and log_debug("upload_file_to_s3" +
                            f"\n | Public url: {public_url}" +
                            f"\n | Final filename: {final_filename}" +
                            f"\n | Error: {error}\n")

    result['public_url'] = public_url
    result['final_filename'] = final_filename
    result['error'] = error is not None
    result['error_message'] = error
    return result


def remove_from_s3(bucket_name: str, key: str) -> dict:
    """
    Remove an object from an S3 bucket.

    Args:
        bucket_name (str): The base path of the S3 bucket.
        key (str): The S3 key of the object to be removed.
    """
    import boto3
    result = get_default_resultset()
    try:
        s3 = boto3.client('s3')
        s3.delete_object(Bucket=bucket_name, Key=key)
        _ = DEBUG and log_debug(
            "remove_from_s3" +
            f"\n | Object removed from S3: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = f"Failed to remove object from S3: {err}"
        log_error(result['error_message'])
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
    import boto3
    result = get_default_resultset()
    try:
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket_name, Key=key)
        # result['content'] = obj['Body'].read().decode('utf-8')
        result['content'] = obj['Body'].read()
        _ = DEBUG and log_debug(
            "get_s3_object" +
            f"\n | Object retrieved from S3: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
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
    import boto3
    result = get_default_resultset()
    if not local_file_path:
        local_file_path = temp_filename(get_file_extension(file_path=key))
    try:
        s3_client = boto3.client('s3')
        s3_client.download_file(bucket_name, key, local_file_path)
        result['local_file_path'] = local_file_path
        _ = DEBUG and log_debug(
            "download_s3_object" +
            f"\n | Object downloaded from S3: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"ERROR-DS3O-010 - Failed to download object: {err}"
        log_error(result['error_message'])
    return result


def get_s3_presigned_url(
    bucket_name: str,
    object_key: str,
    expiration_seconds: Union[
        int, str,
        None] = None
):
    import boto3
    s3_client = boto3.client('s3')
    result = get_default_resultset()
    expires_in = get_storage_presigned_expiration_seconds(
        expiration_seconds)
    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expires_in,
        )
        presigned_url = unquote(presigned_url)
        _ = DEBUG and log_debug(
            "get_s3_presigned_url" +
            f"\n | Bucket: {bucket_name}" +
            f"\n | Object key: {object_key}" +
            f"\n | Expiration seconds: {expires_in}" +
            f"\n | Presigned URL generated: {presigned_url}")
        result['url'] = presigned_url
        return result
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"ERROR-GPSU-010 - Failed to generate presigned url: {err}"
        log_error(result['error_message'])
        return result


def storage_retieval(
    item_id: Union[str, None],
    other_params: Optional[dict] = None,
) -> dict:
    """
    Get S3 bucket content from encrypted item_id
    Args:
        item_id (str, optional): The item_id with the encrypted elements
            (bucket_name, separator and key). Defaults to None.
        other_params (dict, optional): Other parameters. Defaults to None.
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

    if not item_id:
        return error_resultset("Item ID is required", "ASR-E1010")

    # Decrypt item_id to get the bucket_name and key (filespec)
    extension = item_id.split('.')[-1] if '.' in item_id else ''
    extension = '.' + extension if extension else ''
    raw_item_id = item_id.rsplit('.', 1)[0] if '.' in item_id else item_id

    # Get bucket name and file path
    try:
        bucket_name, key = get_bucket_key_from_decripted_item_id(raw_item_id)
    except Exception as err:  # pylint: disable=broad-except
        return error_resultset(str(err), "ASR-E1020")

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
    Prepares the asset URL (image, sound, file) on message content for tools
    like the GPT4 vision.
    Args:
        public_url (str): The public URL of the asset. E.g.:
            https://<bucket-name>.s3.amazonaws.com/<user-id>/<file-name.jpg>
    Returns:
        str: The prepared asset URL.
    """
    final_public_url = public_url

    bucket_name, key = get_bucket_key_from_url(public_url)
    presigned_url_result = get_s3_presigned_url(bucket_name, key)

    if presigned_url_result['error']:
        log_error(final_public_url)
        raise Exception(presigned_url_result['error_message'])
    else:
        final_public_url = presigned_url_result['url']

    _ = DEBUG and log_debug(
        "prepare_asset_url" +
        f"\n\t | public_url: {public_url}"
        f"\n\t | bucket_name: {bucket_name}"
        f"\n\t | key: {key}"
        f"\n\t | presigned_url_result: {presigned_url_result}"
        f"\n\t | final_public_url: {final_public_url}")

    return final_public_url
