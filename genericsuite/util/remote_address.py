"""
Client IP resolution for rate limiting.

By default the direct TCP peer address is used, since it cannot be
spoofed via headers. When the app is known to run behind N trusted
reverse proxies that append to X-Forwarded-For (e.g. an AWS ALB, or
ALB behind CloudFront), set RATE_LIMIT_TRUSTED_PROXY_HOPS=N so the
real client IP -- the N-th entry from the right, appended by the
trusted infrastructure -- is used instead. Entries to the left of
that are client-controlled and must never be trusted.
"""
import os
from typing import Optional


def get_trusted_proxy_hops() -> int:
    """
    Number of trusted reverse-proxy hops in front of this app, read from
    RATE_LIMIT_TRUSTED_PROXY_HOPS (default "0", meaning "don't trust
    X-Forwarded-For at all; use the direct socket peer address").
    """
    try:
        raw_value = os.environ.get('RATE_LIMIT_TRUSTED_PROXY_HOPS', '0')
        return max(0, int(raw_value))
    except ValueError:
        return 0


def resolve_client_ip(
    direct_peer: Optional[str],
    forwarded_for: Optional[str],
) -> str:
    """
    Resolve the client IP address to use as the rate-limiting key.

    Args:
        direct_peer (str | None): The direct TCP peer address seen by
            the app (e.g. request.client.host / request.remote_addr).
        forwarded_for (str | None): The raw X-Forwarded-For header
            value, if present.

    Returns:
        str: The resolved client IP, or "127.0.0.1" if none is found.
    """
    hops = get_trusted_proxy_hops()
    if hops > 0 and forwarded_for:
        chain = [
            addr.strip() for addr in forwarded_for.split(',') if addr.strip()
        ]
        if len(chain) >= hops:
            return chain[-hops]
    return direct_peer or "127.0.0.1"
