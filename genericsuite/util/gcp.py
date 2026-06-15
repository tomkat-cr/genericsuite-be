"""
GCP Cloud Storage Utilities
"""
from typing import Optional, Union
import os
from datetime import timedelta
from urllib.parse import urlparse

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


DEBUG = os.environ.get('CLOUD_GCP_DEBUG', '0') == '1'

CLOUD_STORAGE_PRESIGNED_ACTIVE = os.environ.get(
    'CLOUD_STORAGE_PRESIGNED_ACTIVE', '1') == '1'


def get_gcs_client():
    """
    Get the GCS client.

    Returns:
        google.cloud.storage.Client: The GCS client instance.
    """
    from google.cloud import storage  # pylint: disable=import-outside-toplevel
    return storage.Client()


def gcp_storage_base_url(bucket_name: str) -> str:
    """
    Returns the GCS base URL (path-style).

    Args:
        bucket_name (str): The GCS bucket name.

    Returns:
        str: The GCS base URL.
    """
    return f"https://storage.googleapis.com/{bucket_name}"


def get_bucket_key_from_url(public_url: str):
    """
    Get the GCS bucket name and key from the public URL.

    Args:
        public_url (str): The public URL, e.g.
            https://storage.googleapis.com/my-bucket/path/to/file.jpg

    Returns:
        tuple: (bucket_name, key)
    """
    parsed_url = urlparse(public_url)
    # path is "/<bucket>/<key…>"
    path_parts = parsed_url.path.lstrip('/').split('/', 1)
    bucket_name = path_parts[0]
    key = path_parts[1] if len(path_parts) > 1 else ''
    return bucket_name, key


def upload_file_to_storage(
    bucket_name: str,
    source_path: str,
    dest_path: str,
    public_file: bool = False
) -> dict:
    """
    Uploads a local file to a GCS bucket.

    Args:
        bucket_name (str): The GCS bucket name.
        source_path (str): The local path of the file.
        dest_path (str): The destination path inside the bucket.
        public_file (bool): True to make the object publicly readable.

    Returns:
        dict: A dict with the following elements:
            public_url (str): The GCS (or encrypted) URL of the uploaded file.
            final_filename (str): The final filename.
            error (bool): True if there was any error.
            error_message (str): The eventual error message.
    """
    error = None
    result = get_default_resultset()

    gcs_client = get_gcs_client()

    try:
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(dest_path)
        blob.upload_from_filename(source_path)
        _ = DEBUG and log_debug(
            "upload_file_to_storage" +
            f"\n | File uploaded successfully to GCS Bucket: {bucket_name}" +
            f"\n | path: {dest_path}")
    except FileNotFoundError:
        error = f"The file {source_path} was not found."
        log_error(error)
    except Exception as err:  # pylint: disable=broad-except
        error = f"Failed to upload file to GCS: {err}"
        log_error(error)

    if public_file and not error:
        try:
            blob.make_public()
            _ = DEBUG and log_debug(
                "upload_file_to_storage" +
                f"\n | Blob '{dest_path}' set to public successfully")
        except Exception as err:  # pylint: disable=broad-except
            # Non-fatal — log but don't abort
            _ = DEBUG and log_debug(
                f"upload_file_to_storage | Failed to set public ACL: {err}")

    if storage_url_encryption_enabled():
        public_url = get_storage_masked_url(bucket_name, dest_path)
    else:
        public_url = f"{gcp_storage_base_url(bucket_name)}/{dest_path}"

    final_filename = os.path.basename(dest_path)

    _ = DEBUG and log_debug("upload_file_to_storage" +
                            f"\n | Public url: {public_url}" +
                            f"\n | Final filename: {final_filename}" +
                            f"\n | Error: {error}\n")

    result['public_url'] = public_url
    result['final_filename'] = final_filename
    result['error'] = error is not None
    result['error_message'] = error
    return result


def remove_from_storage(bucket_name: str, key: str) -> dict:
    """
    Remove an object from a GCS bucket.

    Args:
        bucket_name (str): The GCS bucket name.
        key (str): The object key to remove.

    Returns:
        dict: Standard result dict.
    """
    result = get_default_resultset()
    try:
        gcs_client = get_gcs_client()
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(key)
        blob.delete()
        _ = DEBUG and log_debug(
            "remove_from_storage" +
            f"\n | Object removed from GCS: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"Failed to remove object from GCS: {err}"
        log_error(result['error_message'])
    return result


def get_gcs_object(bucket_name: str, key: str) -> dict:
    """
    Get an object from a GCS bucket.

    Args:
        bucket_name (str): The GCS bucket name.
        key (str): The object key to retrieve.

    Returns:
        dict: Standard result dict with raw bytes in 'content'.
    """
    result = get_default_resultset()
    try:
        gcs_client = get_gcs_client()
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(key)
        result['content'] = blob.download_as_bytes()
        _ = DEBUG and log_debug(
            "get_gcs_object" +
            f"\n | Object retrieved from GCS: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"Failed to retrieve object from GCS: {err}"
        log_error(result['error_message'])
    return result


def download_gcs_object(bucket_name: str, key: str,
                        local_file_path: Optional[str] = None) -> dict:
    """
    Download an object from a GCS bucket to a local path.

    Args:
        bucket_name (str): The GCS bucket name.
        key (str): The object key to download.
        local_file_path (str, optional): Destination path. Auto-generated
            when None.

    Returns:
        dict: Standard result dict with 'local_file_path' on success.
    """
    result = get_default_resultset()
    if not local_file_path:
        local_file_path = temp_filename(get_file_extension(file_path=key))
    try:
        gcs_client = get_gcs_client()
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(key)
        blob.download_to_filename(local_file_path)
        result['local_file_path'] = local_file_path
        _ = DEBUG and log_debug(
            "download_gcs_object" +
            f"\n | Object downloaded from GCS: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"ERROR-DGCSO-010 - Failed to download object: {err}"
        log_error(result['error_message'])
    return result


def get_gcs_presigned_url(
    bucket_name: str,
    object_key: str,
    expiration_seconds: Union[int, str, None] = None,
) -> dict:
    """
    Generate a v4 signed URL for a GCS object.

    Args:
        bucket_name (str): The GCS bucket name.
        object_key (str): The object key.
        expiration_seconds (int | str | None): TTL; defaults to
            get_storage_presigned_expiration_seconds().

    Returns:
        dict: Standard result dict with 'url' on success.
    """
    result = get_default_resultset()
    expires_in = get_storage_presigned_expiration_seconds(expiration_seconds)
    try:
        gcs_client = get_gcs_client()
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(object_key)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_in),
            method="GET",
            response_type=get_mime_type(object_key),
        )
        _ = DEBUG and log_debug(
            "get_gcs_presigned_url" +
            f"\n | Bucket: {bucket_name}" +
            f"\n | Object key: {object_key}" +
            f"\n | Expiration seconds: {expires_in}" +
            f"\n | Presigned URL generated: {signed_url}")
        result['url'] = signed_url
        return result
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"ERROR-GGPSU-010 - Failed to generate presigned url: {err}"
        log_error(result['error_message'])
        return result


def storage_retieval(
    item_id: Union[str, None],
    other_params: Optional[dict] = None,
) -> dict:
    """
    Get GCS bucket content from encrypted item_id.

    Args:
        item_id (str | None): Encrypted item_id (bucket_name + separator + key).
        other_params (dict, optional): Extra options; 'mode' can be 'get'
            (default) or 'download'.

    Returns:
        dict: Standard result dict with 'content' (get mode) or
            'local_file_path' (download mode), plus 'mime_type' and 'filename'.
    """
    if other_params is None:
        other_params = {}
    if not other_params.get('mode'):
        other_params['mode'] = 'get'

    if not item_id:
        return error_resultset("Item ID is required", "GSR-E1010")

    extension = item_id.split('.')[-1] if '.' in item_id else ''
    extension = '.' + extension if extension else ''
    raw_item_id = item_id.rsplit('.', 1)[0] if '.' in item_id else item_id

    try:
        bucket_name, key = get_bucket_key_from_decripted_item_id(raw_item_id)
    except Exception as err:  # pylint: disable=broad-except
        return error_resultset(str(err), "GSR-E1020")

    key = key + extension

    if DEBUG:
        log_debug(f">> bucket_name: {bucket_name} | key: {key}")

    if other_params['mode'] == 'get':
        retrieval_resultset = get_gcs_object(bucket_name=bucket_name, key=key)
    else:
        retrieval_resultset = download_gcs_object(
            bucket_name=bucket_name, key=key)

    if retrieval_resultset.get('error'):
        return error_resultset(retrieval_resultset['error_message'],
                               "GSR-E1030")
    retrieval_resultset['mime_type'] = get_mime_type(key)
    retrieval_resultset['filename'] = key
    return retrieval_resultset


def prepare_asset_url(public_url: str) -> str:
    """
    Prepares the GCS asset URL for AI tools like GPT-4 vision.

    When CLOUD_STORAGE_PRESIGNED_ACTIVE=1 a signed URL is returned.
    When CLOUD_STORAGE_PRESIGNED_ACTIVE=0 the original URL is returned.

    Args:
        public_url (str): The public GCS URL.

    Returns:
        str: The (possibly signed) asset URL.
    """
    final_public_url = public_url

    if not CLOUD_STORAGE_PRESIGNED_ACTIVE:
        return final_public_url

    bucket_name, key = get_bucket_key_from_url(public_url)
    presigned_url_result = get_gcs_presigned_url(bucket_name, key)

    if presigned_url_result['error']:
        log_error(final_public_url)
        raise Exception(presigned_url_result['error_message'])

    final_public_url = presigned_url_result['url']

    _ = DEBUG and log_debug(
        "prepare_asset_url" +
        f"\n\t | public_url: {public_url}"
        f"\n\t | bucket_name: {bucket_name}"
        f"\n\t | key: {key}"
        f"\n\t | presigned_url_result: {presigned_url_result}"
        f"\n\t | final_public_url: {final_public_url}")

    return final_public_url
