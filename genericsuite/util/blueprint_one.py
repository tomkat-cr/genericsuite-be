"""
Blueprint wrapper to add authorization, other data and schema validation
to requests.
"""
from typing import Any, Callable, Optional
from functools import partial, wraps
from logging import Logger

from marshmallow import Schema, ValidationError

# from chalice import Chalice
# from chalice.app import Blueprint, Request
from genericsuite.util.framework_abs_layer import Blueprint, Request
from genericsuite.util.utilities import log_debug

# from lib.exceptions import QueryError

DEBUG = False


def validate_schema(
    schema: Schema, data: dict, localized_logger: Logger
) -> dict:
    """
    Validate the input data against the provided schema.

    Args:
        schema (Schema): The schema to validate against.
        data (dict): The input data to be validated.
        localized_logger (Logger): The logger to log validation errors.

    Returns:
        dict: The validated data.

    Raises:
        ValidationError: If the input data does not conform to the schema.
    """
    try:
        return schema.load(data)
    except ValidationError as error:
        localized_logger.error(f'Query error: {error.messages}')
        # raise QueryError(str(error.messages)) from error
    return None


class BlueprintOne(Blueprint):
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
    def route(
        self,
        path: str,
        schema: Optional[Schema] = None,
        authorizor: Optional[Callable[[Request], Request]] = None,
        other_params: Optional[dict] = None,
        **kwargs: Any,
    ) -> Callable:
        def _wrap_inner(register: Callable, route: Callable) -> Callable:
            @wraps(route)
            def _inner(*args: Any, **kwargs: Any) -> Callable:
                app = self.current_app
                request = app.current_request
                if DEBUG:
                    # app.log.info(
                    log_debug(
                        'Request was made to: ' +
                        f'{request.context.get("resourcePath", path)}, ' +
                        f'HTTP method: {request.method}'
                    )
                if schema:
                    validate_schema(schema, request.json_body, app.log)
                if authorizor is not None:
                    request = authorizor(request)
                    if DEBUG:
                        log_debug(
                            'RESPONSE AUTHORIZOR BlueprintOne._wrap_inner' +
                            ' | request:'
                        )
                        log_debug(request.to_dict())
                    auth_response = request.to_dict()
                    if 'statusCode' in auth_response \
                            and auth_response['statusCode'] != 200:
                        if DEBUG:
                            log_debug(
                                'RESPONSE AUTHORIZOR FAILED | request.' +
                                'statusCode'
                            )
                            log_debug(request.to_dict()["statusCode"])
                        return request

                if DEBUG:
                    log_debug('RESPONSE AUTHORIZOR OK')
                kwargs['other_params'] = other_params
                return route(request, *args, **kwargs)

            return register(_inner)

        _register_handler = self._create_registration_function(
            handler_type='route',
            name=kwargs.pop('name', None),
            registration_kwargs={
                'path': path,
                'kwargs': kwargs
            },
        )

        # log_debug(f'ENTERING BlueprintOne.route... {path}')
        return partial(_wrap_inner, _register_handler)

    def get_current_app(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        return self.current_app
