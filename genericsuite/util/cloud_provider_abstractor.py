"""
Cloud Provider Abstractor

IMPORTANT:
* It cannot use configs.py because it is used by config_from_db.py to
* It cannot use app_context, to avoid cycling imports.
"""
import os


def get_cloud_provider() -> str:
    """
    Returns the cloud provider.
    """
    cloud_provider = os.environ.get("CLOUD_PROVIDER")
    if not cloud_provider:
        raise Exception("ERROR: CLOUD_PROVIDER not set [CPA-GCPV-E010]")
    cloud_provider = str(cloud_provider).upper()
    if cloud_provider not in ["AWS", "GCP", "AZURE"]:
        raise Exception(
            f"ERROR: CLOUD_PROVIDER '{cloud_provider}' not supported"
            " [CPA-GCPV-E020]")
    return cloud_provider


def get_cloud_region() -> str:
    """
    Returns the cloud region.
    """
    cloud_provider = get_cloud_provider()
    if cloud_provider == "AWS":
        region = os.environ.get('AWS_REGION')
    elif cloud_provider == "AZURE":
        region = os.environ.get('AZURE_REGION', 'global')
    elif cloud_provider == "GCP":
        region = os.environ.get('GCP_REGION', 'global')
    if not region:
        raise Exception(
            f"ERROR: {cloud_provider} region not set [CPA-GCR-E010]")
    return region
