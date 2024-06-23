"""
This module contains functions for interacting with GCP Secrets Manager.
IMPORTANT:
* It cannot use configs.py because it is used by config_from_db.py to
* It cannot use app_context, to avoid cycling imports.
"""
import os
import json


DEBUG = False
TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')


def get_secrets(secret_name: str, region_name: str,
                get_default_resultset: callable, logger: callable) -> dict:
    """
    Get a secret from GCP Secrets Manager.
    """
    _ = DEBUG and logger.debug(
        f'GCP get_secrets | secret_name: {secret_name}'
        f' | region_name: {region_name}')
    result = get_default_resultset()
    result['resultset'] = {}
    return result


def get_secrets_cache_filename() -> str:
    """
    Get the filename for the secrets cache.
    """
    app_name = os.environ.get('APP_NAME')
    app_stage = os.environ.get('APP_STAGE')
    if not app_name or not app_stage:
        error_message = 'ERROR: Missing environment variables' + \
            ' APP_NAME, APP_STAGE [G-ACF-E010]'
        raise Exception(error_message)
    return os.path.join(
        TEMP_DIR, f's_ec_{app_name.lower()}_{app_stage.lower()}_gcp.json')


def get_cache_secret(get_default_resultset: callable, logger: callable
                     ) -> dict:
    """
    Try to get the secrets from the secrets cache file.
    If it doesn't exist, create it from GCP Secrets.
    """
    app_name = os.environ.get('APP_NAME')
    app_stage = os.environ.get('APP_STAGE')
    region_name = os.environ.get('GCP_REGION')
    result = get_default_resultset()
    if not app_name or not app_stage or not region_name:
        result['error'] = True
        result['error_message'] = 'ERROR: Missing environment variables' + \
            ' (APP_NAME, APP_STAGE, GCP_REGION) [G-ACF-E020]'
        return result
    secret_name = f'{app_name.lower()}-{app_stage.lower()}'
    secrets_cache_filename = get_secrets_cache_filename()
    _ = DEBUG and logger.debug(
        f'GCP get_cache_secret | secret_name: {secret_name}'
        f' | secrets_cache_filename: {secrets_cache_filename}' +
        f' | region_name: {region_name}')
    if os.path.exists(secrets_cache_filename):
        with open(secrets_cache_filename, 'r') as f:
            result['resultset'] = json.load(f)
    else:
        result = get_secrets(secret_name, region_name, get_default_resultset,
                             logger)
        if not result['error']:
            with open(secrets_cache_filename, 'w') as f:
                json.dump(result['resultset'], f)
    return result
