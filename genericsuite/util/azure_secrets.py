"""
This module contains functions for interacting with AZURE Secrets Manager.
IMPORTANT:
* It cannot use configs.py because it is used by config_from_db.py to
* It cannot use app_context, to avoid cycling imports.
"""
from typing import Callable
import os
import json


DEBUG = False
TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')


def get_secrets(secret_name: str, region_name: str,
                get_default_resultset: Callable, logger: Callable) -> dict:
    """
    Get a secret from AZURE Secrets Manager.
    """
    _ = DEBUG and logger.debug(
        f'AZURE get_secrets | secret_name: {secret_name}'
        f' | region_name: {region_name}')
    result = get_default_resultset()
    result['resultset'] = {}
    return result


def get_secrets_cache_filename(secret_type: str = "") -> str:
    """
    Get the filename for the secrets cache.
    """
    app_name = os.environ.get('APP_NAME')
    app_stage = os.environ.get('APP_STAGE')
    if not app_name or not app_stage:
        error_message = 'ERROR: Missing environment variables' + \
            ' APP_NAME, APP_STAGE [G-ACF-E010]'
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
                  f'{app_stage.lower()}_azure.json')


def get_cache_secret(get_default_resultset: Callable, logger: Callable
                     ) -> dict:
    """
    Try to get the secrets from the secrets cache file.
    If it doesn't exist, create it from AZURE Secrets.
    """
    app_name = os.environ.get('APP_NAME')
    app_stage = os.environ.get('APP_STAGE')
    region_name = os.environ.get('AZURE_REGION')
    result = get_default_resultset()
    if not app_name or not app_stage or not region_name:
        result['error'] = True
        result['error_message'] = 'ERROR: Missing environment variables' + \
            ' (APP_NAME, APP_STAGE, AZURE_REGION) [G-ACF-E020]'
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
        _ = DEBUG and logger.debug(
            f'AWS get_cache_secret | secret_name: {secret_name}'
            f' | secrets_cache_filename: {secrets_cache_filename}' +
            f' | region_name: {region_name}')
        if os.path.exists(secrets_cache_filename):
            with open(secrets_cache_filename, 'r', encoding="utf-8") as f:
                result['resultset'].update(json.load(f))
        else:
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
