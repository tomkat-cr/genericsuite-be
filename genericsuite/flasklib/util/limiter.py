# Rate limiting — shared across all routes that use @limiter.limit(...)
# Flask rate limiting with SlowAPI is not directly supported; instead,
# use Flask-Limiter for Flask integration.
# Replace SlowAPI with Flask-Limiter usage.
from flask import Flask
from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def get_flask_limiter(app: Flask) -> Limiter:
    """
    Get the Flask limiter instance.
    """
    return Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
    )
