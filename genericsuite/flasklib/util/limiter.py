# Rate limiting — shared across all routes that use @limiter.limit(...)
# Flask rate limiting with SlowAPI is not directly supported; instead,
# use Flask-Limiter for Flask integration.
# Replace SlowAPI with Flask-Limiter usage.
from flask import Flask, request
from flask_limiter import Limiter

from genericsuite.util.remote_address import resolve_client_ip


def get_remote_address() -> str:
    """
    Rate-limiting key function. Trusts X-Forwarded-For only up to the
    hop count configured via RATE_LIMIT_TRUSTED_PROXY_HOPS; see
    genericsuite.util.remote_address for the trust model.
    """
    return resolve_client_ip(
        request.remote_addr, request.headers.get('X-Forwarded-For'))


def get_flask_limiter(app: Flask) -> Limiter:
    """
    Get the Flask limiter instance.
    """
    return Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
    )
