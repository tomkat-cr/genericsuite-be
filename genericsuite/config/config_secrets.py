"""
Secrets config management
"""
from typing import Callable
import os

from genericsuite.util.cloud_provider_abstractor import get_cloud_provider

from genericsuite.util.aws_secrets import (
    get_cache_secret as get_aws_secrets,
    get_secrets_cache_filename as get_aws_cache_filename,
)
from genericsuite.util.gcp_secrets import (
    get_cache_secret as get_gcp_secrets,
    get_secrets_cache_filename as get_gcp_cache_filename,
)
from genericsuite.util.azure_secrets import (
    get_cache_secret as get_azure_secrets,
    get_secrets_cache_filename as get_azure_cache_filename,
)

DEBUG = False


def get_secrets_from_iaas(get_default_resultset: Callable, logger: Callable
                          ) -> dict:
    """
    Get secrets from the iaas (AWS, GCP, Azure) and set environment variables.

    If the GET_SECRETS_ENABLED environment variable is "1" (default value),
    there must be environment variables set for:
        CLOUD_PROVIDER, APP_NAME, APP_STAGE,
        AWS_REGION or GCP_REGION or AZURE_REGION
    and the mandatory environment variables must be defined in the cloud
    provider secrets manager.
    Check the script "scripts/aws_secrets/aws_secrets_manager.sh" in the
    GenericSuite Backend Scripts package for more information.

    If GET_SECRETS_ENABLED is not "1", the mandatory environment variables
    must be set:
        APP_DB_URI, APP_SUPERADMIN_EMAIL, APP_DB_NAME, APP_DB_ENGINE,
        APP_NAME, APP_SECRET_KEY, APP_HOST_NAME, STORAGE_URL_SEED,
        GIT_SUBMODULE_LOCAL_PATH
    """
    result = get_default_resultset()
    if os.environ.get("GET_SECRETS_ENABLED", "1") != "1":
        _ = DEBUG and logger.debug("GET_SECRETS_ENABLED set to 0..." +
                                   " getting all envvars from environment")
        return result

    try:
        cloud_provider = get_cloud_provider()
    except Exception as e:
        result["error"] = True
        result["error_message"] = str(e)
        return result

    if cloud_provider.upper() == "AWS":
        iaas_secrets = get_aws_secrets(get_default_resultset, logger)
    elif cloud_provider.upper() == "GCP":
        iaas_secrets = get_gcp_secrets(get_default_resultset, logger)
    elif cloud_provider.upper() == "AZURE":
        iaas_secrets = get_azure_secrets(get_default_resultset, logger)

    if iaas_secrets["error"]:
        return iaas_secrets
    for key, value in iaas_secrets["resultset"].items():
        _ = DEBUG and logger.debug(f"EnvVar {key} = {value}")
        os.environ[key] = value
    return result


def get_secrets_cache_filename(secret_type: str = "") -> str:
    """
    Get secrets cache filename
    """
    cloud_provider = get_cloud_provider()
    filename = None
    if cloud_provider.upper() == "AWS":
        filename = get_aws_cache_filename(secret_type)
    elif cloud_provider.upper() == "GCP":
        filename = get_gcp_cache_filename(secret_type)
    elif cloud_provider.upper() == "AZURE":
        filename = get_azure_cache_filename(secret_type)
    return filename
