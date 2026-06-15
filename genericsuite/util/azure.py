"""
Azure Blob Storage Utilities
"""
from typing import Optional, Union
import os
from datetime import datetime, timedelta, timezone
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


DEBUG = os.environ.get('CLOUD_AZURE_DEBUG', '0') == '1'

CLOUD_STORAGE_PRESIGNED_ACTIVE = os.environ.get(
    'CLOUD_STORAGE_PRESIGNED_ACTIVE', '1') == '1'


def get_blob_service_client():
    """
    Get an Azure BlobServiceClient.

    Tries AZURE_STORAGE_CONNECTION_STRING first; falls back to
    AZURE_STORAGE_ACCOUNT_NAME + AZURE_STORAGE_ACCOUNT_KEY.

    Returns:
        azure.storage.blob.BlobServiceClient: The service client.
    """
    from azure.storage.blob import BlobServiceClient  # pylint: disable=import-outside-toplevel
    conn_str = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    if conn_str:
        return BlobServiceClient.from_connection_string(conn_str)
    account_name = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')
    account_key = os.environ.get('AZURE_STORAGE_ACCOUNT_KEY')
    account_url = f"https://{account_name}.blob.core.windows.net"
    from azure.storage.blob import BlobServiceClient as _BSC  # pylint: disable=import-outside-toplevel
    return _BSC(account_url=account_url, credential=account_key)


def blob_storage_base_url(bucket_name: str) -> str:
    """
    Returns the Azure Blob Storage base URL for a container.

    Args:
        bucket_name (str): The container name (used as "bucket").

    Returns:
        str: The Azure Blob base URL.
    """
    account_name = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME', bucket_name)
    return f"https://{account_name}.blob.core.windows.net/{bucket_name}"


def get_bucket_key_from_url(public_url: str):
    """
    Get the Azure container name and blob key from a public URL.

    Args:
        public_url (str): URL of the form
            https://{account}.blob.core.windows.net/{container}/{key}

    Returns:
        tuple: (container_name, key)
    """
    parsed_url = urlparse(public_url)
    # path is "/<container>/<key…>"
    path_parts = parsed_url.path.lstrip('/').split('/', 1)
    container_name = path_parts[0]
    key = path_parts[1] if len(path_parts) > 1 else ''
    return container_name, key


def upload_file_to_storage(
    bucket_name: str,
    source_path: str,
    dest_path: str,
    public_file: bool = False
) -> dict:
    """
    Uploads a local file to an Azure Blob Storage container.

    Args:
        bucket_name (str): The Azure container name.
        source_path (str): The local path of the file.
        dest_path (str): The destination blob path inside the container.
        public_file (bool): Unused (Azure public access is set at container
            level, not per-blob via this API).

    Returns:
        dict: A dict with the following elements:
            public_url (str): The Azure Blob (or encrypted) URL of the
                uploaded file.
            final_filename (str): The final filename.
            error (bool): True if there was any error.
            error_message (str): The eventual error message.
    """
    error = None
    result = get_default_resultset()

    try:
        blob_client = get_blob_service_client()
        container_client = blob_client.get_container_client(bucket_name)
        with open(source_path, 'rb') as data:
            container_client.upload_blob(
                name=dest_path, data=data, overwrite=True)
        _ = DEBUG and log_debug(
            "upload_file_to_storage" +
            f"\n | File uploaded to Azure container: {bucket_name}" +
            f"\n | path: {dest_path}")
    except FileNotFoundError:
        error = f"The file {source_path} was not found."
        log_error(error)
    except Exception as err:  # pylint: disable=broad-except
        error = f"Failed to upload file to Azure Blob Storage: {err}"
        log_error(error)

    if storage_url_encryption_enabled():
        public_url = get_storage_masked_url(bucket_name, dest_path)
    else:
        account_name = os.environ.get(
            'AZURE_STORAGE_ACCOUNT_NAME', bucket_name)
        public_url = (
            f"https://{account_name}.blob.core.windows.net"
            f"/{bucket_name}/{dest_path}"
        )

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
    Remove an object from an Azure Blob Storage container.

    Args:
        bucket_name (str): The Azure container name.
        key (str): The blob key to remove.

    Returns:
        dict: Standard result dict.
    """
    result = get_default_resultset()
    try:
        blob_client = get_blob_service_client()
        blob = blob_client.get_blob_client(
            container=bucket_name, blob=key)
        blob.delete_blob()
        _ = DEBUG and log_debug(
            "remove_from_storage" +
            f"\n | Blob removed from Azure: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"Failed to remove blob from Azure: {err}"
        log_error(result['error_message'])
    return result


def get_blob_object(bucket_name: str, key: str) -> dict:
    """
    Get a blob from Azure Blob Storage.

    Args:
        bucket_name (str): The Azure container name.
        key (str): The blob key to retrieve.

    Returns:
        dict: Standard result dict with raw bytes in 'content'.
    """
    result = get_default_resultset()
    try:
        blob_client = get_blob_service_client()
        blob = blob_client.get_blob_client(
            container=bucket_name, blob=key)
        download_stream = blob.download_blob()
        result['content'] = download_stream.readall()
        _ = DEBUG and log_debug(
            "get_blob_object" +
            f"\n | Blob retrieved from Azure: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"Failed to retrieve blob from Azure: {err}"
        log_error(result['error_message'])
    return result


def download_blob_object(bucket_name: str, key: str,
                         local_file_path: Optional[str] = None) -> dict:
    """
    Download a blob from Azure Blob Storage to a local path.

    Args:
        bucket_name (str): The Azure container name.
        key (str): The blob key to download.
        local_file_path (str, optional): Destination path. Auto-generated
            when None.

    Returns:
        dict: Standard result dict with 'local_file_path' on success.
    """
    result = get_default_resultset()
    if not local_file_path:
        local_file_path = temp_filename(get_file_extension(file_path=key))
    try:
        blob_client = get_blob_service_client()
        blob = blob_client.get_blob_client(
            container=bucket_name, blob=key)
        with open(local_file_path, 'wb') as f_handler:
            download_stream = blob.download_blob()
            f_handler.write(download_stream.readall())
        result['local_file_path'] = local_file_path
        _ = DEBUG and log_debug(
            "download_blob_object" +
            f"\n | Blob downloaded from Azure: {bucket_name}/{key}")
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"ERROR-DAZBO-010 - Failed to download blob: {err}"
        log_error(result['error_message'])
    return result


def get_blob_presigned_url(
    bucket_name: str,
    object_key: str,
    expiration_seconds: Union[int, str, None] = None,
) -> dict:
    """
    Generate a SAS (shared access signature) URL for a blob.

    Args:
        bucket_name (str): The Azure container name.
        object_key (str): The blob key.
        expiration_seconds (int | str | None): TTL; defaults to
            get_storage_presigned_expiration_seconds().

    Returns:
        dict: Standard result dict with 'url' on success.
    """
    result = get_default_resultset()
    expires_in = get_storage_presigned_expiration_seconds(expiration_seconds)
    try:
        from azure.storage.blob import (  # pylint: disable=import-outside-toplevel
            generate_blob_sas,
            BlobSasPermissions,
        )
        account_name = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')
        account_key = os.environ.get('AZURE_STORAGE_ACCOUNT_KEY')
        if not account_name or not account_key:
            result['error'] = True
            result['error_message'] = (
                "ERROR-GABPU-010 - AZURE_STORAGE_ACCOUNT_NAME and "
                "AZURE_STORAGE_ACCOUNT_KEY are required for SAS URL generation"
            )
            log_error(result['error_message'])
            return result

        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=bucket_name,
            blob_name=object_key,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
            content_type=get_mime_type(object_key),
        )
        sas_url = (
            f"https://{account_name}.blob.core.windows.net"
            f"/{bucket_name}/{object_key}?{sas_token}"
        )
        _ = DEBUG and log_debug(
            "get_blob_presigned_url" +
            f"\n | Container: {bucket_name}" +
            f"\n | Object key: {object_key}" +
            f"\n | Expiration seconds: {expires_in}" +
            f"\n | SAS URL generated: {sas_url}")
        result['url'] = sas_url
        return result
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = \
            f"ERROR-GABPU-010 - Failed to generate SAS URL: {err}"
        log_error(result['error_message'])
        return result


def storage_retieval(
    item_id: Union[str, None],
    other_params: Optional[dict] = None,
) -> dict:
    """
    Get Azure Blob Storage content from encrypted item_id.

    Args:
        item_id (str | None): Encrypted item_id (container + separator + key).
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
        return error_resultset("Item ID is required", "AZSR-E1010")

    extension = item_id.split('.')[-1] if '.' in item_id else ''
    extension = '.' + extension if extension else ''
    raw_item_id = item_id.rsplit('.', 1)[0] if '.' in item_id else item_id

    try:
        bucket_name, key = get_bucket_key_from_decripted_item_id(raw_item_id)
    except Exception as err:  # pylint: disable=broad-except
        return error_resultset(str(err), "AZSR-E1020")

    key = key + extension

    if DEBUG:
        log_debug(f">> bucket_name: {bucket_name} | key: {key}")

    if other_params['mode'] == 'get':
        retrieval_resultset = get_blob_object(
            bucket_name=bucket_name, key=key)
    else:
        retrieval_resultset = download_blob_object(
            bucket_name=bucket_name, key=key)

    if retrieval_resultset.get('error'):
        return error_resultset(retrieval_resultset['error_message'],
                               "AZSR-E1030")
    retrieval_resultset['mime_type'] = get_mime_type(key)
    retrieval_resultset['filename'] = key
    return retrieval_resultset


def prepare_asset_url(public_url: str) -> str:
    """
    Prepares the Azure Blob asset URL for AI tools like GPT-4 vision.

    When CLOUD_STORAGE_PRESIGNED_ACTIVE=1 a SAS URL is returned.
    When CLOUD_STORAGE_PRESIGNED_ACTIVE=0 the original URL is returned.

    Args:
        public_url (str): The public Azure Blob URL.

    Returns:
        str: The (possibly SAS-signed) asset URL.
    """
    final_public_url = public_url

    if not CLOUD_STORAGE_PRESIGNED_ACTIVE:
        return final_public_url

    bucket_name, key = get_bucket_key_from_url(public_url)
    presigned_url_result = get_blob_presigned_url(bucket_name, key)

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
