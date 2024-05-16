"""
Blueprint wrapper to add authorization, other data and schema validation
to requests.
"""
from typing import Any, Callable, Optional
from functools import partial, wraps

from chalice.app import Blueprint, Request
# from genericsuite.util.framework_abs_layer import Blueprint, Request
from genericsuite.util.app_logger import log_debug
from genericsuite.util.schema_utilities import Schema, schema_verification


DEBUG = False


class BlueprintOne(Blueprint):
    """
    Class to register a new route with optional schema validation and authorization.
    """

    def get_current_app(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        return self.current_app

    def get_current_request(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        return self.current_app.current_request

    def route(
        self,
        path: str,
        authorizor: Optional[Callable[[Request], Request]] = None,
        schema: Optional[Schema] = None,
        other_params: Optional[dict] = None,
        **kwargs: Any,
    ) -> Callable:
        """
        Register a new route with optional schema validation and authorization.

        Args:
            path (str): The URL path for the route.
            schema (Optional[Schema]): The schema to validate the request against.
            authorizor (Optional[Callable[[Request], Request]]): The authorization
            function.
            other_params (Optional[dict]): Additional parameters to pass to the
            route.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            Callable: The registered route function.
        """
        def route_wrapper(register: Callable, route: Callable) -> Callable:
            @wraps(route)
            def route_processor(*args: Any, **kwargs: Any) -> Callable:
                current_app = self.get_current_app()
                current_request = self.get_current_request()
                if DEBUG:
                    log_debug(
                        'Request was made to: ' +
                        f'{current_request.context.get("resourcePath", path)}, ' +
                        f'HTTP method: {current_request.method}'
                    )
                if schema:
                    schema_verification(current_request.json_body, schema, current_app.log)
                if authorizor is not None:
                    current_request = authorizor(current_request)
                    if DEBUG:
                        log_debug(
                            'RESPONSE AUTHORIZOR BlueprintOne.route_wrapper' +
                            ' | current_request:'
                        )
                        log_debug(current_request.to_dict())
                    auth_response = current_request.to_dict()
                    if 'statusCode' in auth_response \
                            and auth_response['statusCode'] != 200:
                        if DEBUG:
                            log_debug(
                                'RESPONSE AUTHORIZOR FAILED | current_request.' +
                                'statusCode'
                            )
                            log_debug(current_request.to_dict()["statusCode"])
                        return current_request

                if DEBUG:
                    log_debug('RESPONSE AUTHORIZOR OK')
                kwargs['other_params'] = other_params
                return route(current_request, *args, **kwargs)

            return register(route_processor)

        handler_final = self._create_registration_function(
            handler_type='route',
            name=kwargs.pop('name', None),
            registration_kwargs={
                'path': path,
                'kwargs': kwargs
            },
        )

        # log_debug(f'ENTERING BlueprintOne.route... {path}')
        return partial(route_wrapper, handler_final)
