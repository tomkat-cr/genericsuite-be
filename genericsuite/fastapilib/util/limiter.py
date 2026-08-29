"""
Rate limiting — shared across all routes that use @limiter.limit(...)
"""
from slowapi import Limiter
from starlette.requests import Request

from genericsuite.util.remote_address import resolve_client_ip


def get_remote_address(request: Request) -> str:
    """
    Rate-limiting key function. Trusts X-Forwarded-For only up to the
    hop count configured via RATE_LIMIT_TRUSTED_PROXY_HOPS; see
    genericsuite.util.remote_address for the trust model.
    """
    direct_peer = request.client.host if request.client else None
    return resolve_client_ip(
        direct_peer, request.headers.get('X-Forwarded-For'))


limiter = Limiter(key_func=get_remote_address)
