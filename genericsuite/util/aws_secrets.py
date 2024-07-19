"""
This module contains functions for interacting with AWS Secrets Manager.
IMPORTANT:
* It cannot use configs.py because it is used by config_from_db.py to
* It cannot use app_context, to avoid cycling imports.
"""
from typing import Callable
import os
import json

import boto3
from botocore.exceptions import ClientError


DEBUG = False
TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')


def get_secrets(secret_name: str, region_name: str,
                get_default_resultset: Callable, logger: Callable) -> dict:
    """
    Get a secret from AWS Secrets Manager.
    """
    _ = DEBUG and logger.debug(f'AWS get_secrets | secret_name: {secret_name}'
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
        result['error_message'] = str(e) + ' [A-ACF-E030]'
        result['secret_name'] = secret_name
        result['region_name'] = region_name
        return result
    secret = get_secret_value_response['SecretString']
    # _ = DEBUG and logger.debug(f'get_secret | secret: {secret}')
    try:
        result['resultset'] = json.loads(secret)
    except ValueError as e:
        result['error'] = True
        result['error_message'] = str(e) + ' [A-ACF-E040]'
    except Exception as e:
        result['error'] = True
        result['error_message'] = str(e) + ' [A-ACF-E050]'
    return result


def get_secrets_cache_filename(secret_type: str = "") -> str:
    """
    Get the filename for the secrets cache.
    """
    app_name = os.environ.get('APP_NAME')
    app_stage = os.environ.get('APP_STAGE')
    if not app_name or not app_stage:
        error_message = 'ERROR: Missing environment variables' + \
            ' APP_NAME, APP_STAGE [A-ACF-E010]'
        raise Exception(error_message)
    prefix = {
        'secrets': 's_ec',
        'envs': 'e_nv'
    }
    if secret_type not in ['secrets', 'envs']:
        error_message = f'ERROR: Invalid secret_type: {secret_type}' + \
            ' [A-ACF-E011]'
        raise Exception(error_message)
    return os.path.join(
        TEMP_DIR, f'{prefix[secret_type]}_{app_name.lower()}_' +
                  f'{app_stage.lower()}_aws.json')


def get_cache_secret(get_default_resultset: Callable, logger: Callable
                     ) -> dict:
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
            ' (APP_NAME, APP_STAGE, AWS_REGION) [A-ACF-E020]'
        return result
    secret_sets = []
    if os.environ.get("GET_SECRETS_CRITICAL", "1") == "1":
        _ = DEBUG and logger.debug("GET_SECRETS_CRITICAL set to 1..." +
                                   " getting secrets from the cloud...")
        secret_sets.append({
            "encrypted": True,
            "secret_name": f'{app_name.lower()}-{app_stage.lower()}-secrets',
            "secrets_cache_filename": get_secrets_cache_filename('secrets')
        })
    else:
        _ = DEBUG and logger.debug("GET_SECRETS_CRITICAL set to 0..." +
                                   " getting secrets from environment...")
    if os.environ.get("GET_SECRETS_ENVVARS", "1") == "1":
        _ = DEBUG and logger.debug("GET_SECRETS_ENVVARS set to 1..." +
                                   " getting envvars from the cloud...")
        secret_sets.append({
            "encrypted": False,
            "secret_name": f'{app_name.lower()}-{app_stage.lower()}-envs',
            "secrets_cache_filename": get_secrets_cache_filename('envs')
        })
    else:
        _ = DEBUG and logger.debug("GET_SECRETS_ENVVARS set to 0..." +
                                   " getting envvars from environment...")
    result['resultset'] = {}
    for secret_set in secret_sets:
        secret_name = secret_set["secret_name"]
        secrets_cache_filename = secret_set["secrets_cache_filename"]
        if os.path.exists(secrets_cache_filename):
            _ = DEBUG and logger.debug(
                f'AWS get_cache_secret | secret_name: {secret_name}'
                f' | FROM secrets_cache_filename: {secrets_cache_filename}')
            with open(secrets_cache_filename, 'r', encoding="utf-8") as f:
                result['resultset'].update(json.load(f))
        else:
            _ = DEBUG and logger.debug(
                f'AWS get_cache_secret | secret_name: {secret_name}' +
                f' | region_name: {region_name}' +
                f' | CREATING cache filename: {secrets_cache_filename}')
            result_inner = get_secrets(
                secret_name, region_name,
                get_default_resultset, logger)
            if result_inner['error']:
                result['error'] = True
                result['error_message'] = result_inner['error_message']
            else:
                with open(secrets_cache_filename, 'w', encoding="utf-8") as f:
                    json.dump(result_inner['resultset'], f)
                result['resultset'].update(result_inner['resultset'])
    return result
