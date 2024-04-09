"""
AWS Utilities
"""
from datetime import datetime
import os
import requests
import json

import boto3
from botocore.exceptions import NoCredentialsError

from genericsuite.util.app_logger import log_debug

DEBUG = False


def upload_nodup_file_to_s3(
    file_path: str,
    original_filename: str,
    bucket_name: str,
    sub_dir: str = None,
    public_file: bool = False,
):
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
):
    """
    Uploads a local file to an S3 bucket.

    Args:
        bucket_name (str): The base path of the S3 bucket.
        source_path (str): The local path of the file.
        dest_path (str): The S3 path of the file.
        public_file (bool): True to make the file public (ACL public-read)

    Returns:
        str: The S3 URL of the uploaded file.
        str: the final filename (with a date/time prefix)
        str: The eventual error message
    """
    error = None

    # Initialize S3 client
    s3_client = boto3.client('s3')

    try:
        # Upload the file
        s3_client.upload_file(
            source_path,
            bucket_name,
            dest_path,
        )
        log_debug("")
        log_debug(f"File uploaded successfully S3 Bucket: {bucket_name}" +
                  f" | path: {dest_path}")
    except FileNotFoundError:
        error = f"The file {source_path} was not found."
        log_debug("")
        log_debug(error)
        # raise
    except NoCredentialsError:
        error = "Credentials not available for S3 upload."
        log_debug("")
        log_debug(error)
        # raise

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
            log_debug("")
            log_debug(error)

    # Return the public S3 URL of the uploaded file
    # public_url = f"https://s3.amazonaws.com/{bucket_name}/{dest_path}"
    public_url = f"https://{bucket_name}.s3.amazonaws.com/{dest_path}"

    # Final filanme is the file name in the S3 destination path.
    final_filename = os.path.basename(dest_path)

    log_debug(f"Public url: {public_url}")
    log_debug(f"Final filename: {final_filename}")
    log_debug(f"Error: {error}")
    log_debug("")

    return public_url, final_filename, error


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
    sub_dir: str = None,
    original_filename: str = None
) -> (str, str, int, str):
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
        attachment_url (str): URL for the image.
        final_filename (str): file name of the image with date/time added.
        file_size (int): the file size in bytes.
        error (str): the eventual error message or None if no errors
    """
    if not original_filename:
        original_filename = url.split('/')[-1]
    response = requests.get(url, timeout=10)    # 10 seconds timeout
    tmp_file_path = '/tmp/' + original_filename
    with open(tmp_file_path, 'wb') as f_handler:
        f_handler.write(response.content)
    file_size = os.stat(tmp_file_path).st_size
    public_url, final_filename, error = upload_nodup_file_to_s3(
        file_path=tmp_file_path,
        original_filename=original_filename,
        bucket_name=bucket_name,
        sub_dir=sub_dir,
    )
    attachment_url = public_url
    os.remove(tmp_file_path)  # Clean up the temporary file
    return attachment_url, final_filename, file_size, error


def remove_from_s3(bucket_name: str, key: str):
    """
    Remove an object from an S3 bucket.

    Args:
        bucket_name (str): The base path of the S3 bucket.
        key (str): The S3 key of the object to be removed.
    """
    s3 = boto3.client('s3')
    s3.delete_object(Bucket=bucket_name, Key=key)
    log_debug(f"Object removed from S3: {bucket_name}/{key}")
    return
