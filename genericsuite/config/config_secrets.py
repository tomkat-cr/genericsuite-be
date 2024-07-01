"""
Secrets config management
"""
from typing import Callable
import os

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
    """
    result = get_default_resultset()
    cloud_provider = os.environ.get("CLOUD_PROVIDER")
    if not cloud_provider:
        result["error"] = True
        result["error_message"] = "ERROR: CLOUD_PROVIDER not set [GSFI-E010]"
        return result
    if cloud_provider.upper() == "AWS":
        iaas_secrets = get_aws_secrets(get_default_resultset, logger)
    elif cloud_provider.upper() == "GCP":
        iaas_secrets = get_gcp_secrets(get_default_resultset, logger)
    elif cloud_provider.upper() == "AZURE":
        iaas_secrets = get_azure_secrets(get_default_resultset, logger)
    else:
        result["error"] = True
        result["error_message"] = \
            "ERROR: CLOUD_PROVIDER not supported [GSFI-E020]"
        return result
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
    cloud_provider = os.environ.get("CLOUD_PROVIDER")
    if not cloud_provider:
        error_message = "ERROR: CLOUD_PROVIDER not set [GSCF-E010]"
        raise Exception(error_message)
    filename = None
    if cloud_provider.upper() == "AWS":
        filename = get_aws_cache_filename(secret_type)
    elif cloud_provider.upper() == "GCP":
        filename = get_gcp_cache_filename(secret_type)
    elif cloud_provider.upper() == "AZURE":
        filename = get_azure_cache_filename(secret_type)
    else:
        error_message = "ERROR: CLOUD_PROVIDER not supported [GSCF-E020]"
        raise Exception(error_message)
    return filename
