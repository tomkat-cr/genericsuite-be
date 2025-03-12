"""
Blueprint wrapper to add authorization, other data and schema validation
to requests for Flask.
"""
from typing import Any, Callable, Optional
from functools import wraps

from flask import Blueprint, current_app
# from flask import request

from genericsuite.util.app_logger import log_debug
from genericsuite.util.schema_utilities import Schema, schema_verification
from genericsuite.util.jwt import AuthorizedRequest
from genericsuite.flasklib.framework_abstraction import Request

DEBUG = False


class BlueprintOne(Blueprint):
    """
    Class to register a new route with optional schema validation and
    authorization.
    """

    def route(
        self,
        rule: str,
        authorizor: Optional[Callable] = None,
        schema: Optional[Schema] = None,
        other_params: Optional[dict] = None,
        **options: Any
    ) -> Callable:
        """
        Register a new route with optional schema validation and authorization.

        Args:
            rule (str): The URL rule for the route.
            authorizor (Optional[Callable]): The authorization function.
            schema (Optional[Schema]): The schema to validate the request
                against.
            other_params (Optional[dict]): Additional parameters to pass to
                the route.
            **options: Additional options to pass to the route.

        Returns:
            Callable: The decorator function.
        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                current_request = Request()
                current_request.set_properties()

                _ = DEBUG and log_debug(
                    f'Request was made to: '
                    f'{current_request.context.get("resourcePath", rule)}'
                    f', HTTP method: {current_request.method}')

                if schema:
                    schema_verification(current_request.json, schema,
                                        current_app.logger)

                if authorizor is not None:
                    current_request = authorizor(current_request)
                    if DEBUG:
                        log_debug(
                            'RESPONSE AUTHORIZOR BlueprintOne.route_wrapper'
                            f'{current_request}')

                    if not isinstance(current_request, AuthorizedRequest):
                        if DEBUG:
                            log_debug('RESPONSE AUTHORIZOR FAILED')
                        return current_request

                if DEBUG:
                    log_debug('RESPONSE AUTHORIZOR OK')

                kwargs['other_params'] = other_params
                return f(current_request, *args, **kwargs)

            return super(BlueprintOne, self).route(rule, **options)(wrapper)

        return decorator

    def get_current_app(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        return current_app

    def get_current_request(self) -> Any:
        """
        Get the current request object. It must be called inside a router
        function.
        """
        current_request = Request()
        current_request.set_properties()
        return current_request
        # return request
