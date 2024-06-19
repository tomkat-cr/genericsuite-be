"""
This module contains functions for interacting with AWS Secrets Manager.
IMPORTANT: It cannot use configs.py because it is used by config_from_db.py to
get the secrets.
"""
import os
import json

import boto3
from botocore.exceptions import ClientError

from genericsuite.util.utilities import get_default_resultset
from genericsuite.util.app_logger import log_debug


DEBUG = True
TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')


def get_secrets(secret_name: str, region_name: str) -> dict:
    """
    Get a secret from AWS Secrets Manager.
    """
    _ = DEBUG and log_debug(f'get_secrets | secret_name: {secret_name}'
                            f' | region_name: {region_name}')
    result = get_default_resultset()
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        result['error'] = True
        result['error_message'] = str(e)
        return result
    secret = get_secret_value_response['SecretString']
    # _ = DEBUG and log_debug(f'get_secret | secret: {secret}')
    try:
        result['resultset'] = json.loads('{' + str(secret) + '}')
    except ValueError as e:
        result['error'] = True
        result['error_message'] = str(e)
    except Exception as e:
        result['error'] = True
        result['error_message'] = str(e)
    return result


def get_secrets_cache_filename() -> str:
    """
    Get the filename for the secrets cache.
    """
    return os.path.join(TEMP_DIR, 's_ec_aws.json')


def get_cache_secret() -> dict:
    """
    Try to get the secrets from the secrets cache file.
    If it doesn't exist, create it from AWS Secrets.
    """
    app_name = os.environ.get('APP_NAME')
    app_stage = os.environ.get('APP_STAGE')
    region_name = os.environ.get('AWS_REGION')
    result = get_default_resultset()
    if not app_name or not app_stage or not region_name:
        result['error'] = True
        result['error_message'] = 'ERROR: Missing environment variables' + \
            ' (APP_NAME, APP_STAGE, AWS_REGION)'
        return result
    secret_name = f'{app_name.lower()}-{app_stage.lower()}'
    secrets_cache_filename = get_secrets_cache_filename()
    _ = DEBUG and log_debug(
        f'get_cache_secret | secret_name: {secret_name}'
        f' | secrets_cache_filename: {secrets_cache_filename}' +
        f' | region_name: {region_name}')
    if os.path.exists(secrets_cache_filename):
        with open(secrets_cache_filename, 'r') as f:
            result['resultset'] = json.load(f)
    else:
        result = get_secrets(secret_name, region_name)
        if not result['error']:
            with open(secrets_cache_filename, 'w') as f:
                json.dump(result['resultset'], f)
    return result
