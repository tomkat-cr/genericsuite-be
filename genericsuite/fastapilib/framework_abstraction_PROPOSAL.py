"""
FastAPI abstraction layer
"""
# from typing import Optional, Union, Dict, Any
from typing import Optional, Dict, Any, Tuple, Callable, List, Union

import os
import importlib
import json

import jwt
from pydantic import BaseModel

from fastapi import Request as FastAPIRequest
from fastapi import Response as FastAPIResponse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

# from genericsuite.fastapilib.util.blueprint_one import (
#     BlueprintOne as FaBlueprintOne
# )

from genericsuite.config.config import (
    Config,
    config_log_debug as log_debug,
    config_log_error as log_error,
)

DEBUG = False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

FRAMEWORK_LOADED = False
FRAMEWORK = os.environ.get('CURRENT_FRAMEWORK', '').lower()
if FRAMEWORK == 'fastapi':
    try:
        framework_module = importlib.import_module(FRAMEWORK)
        FRAMEWORK_LOADED = True
        if DEBUG:
            print(f'FastAPI abstraction | framework_module: {framework_module}')


        class FrameworkClass(framework_module.FastAPI):
            """
            Framkework class cloned from the selected framework super class.
            """


        class Request(BaseModel):
            """
            Request class cloned from the selected Request framework super class.
            This class is the one to be imported by the project modules
            """
            method: Optional[str] = "GET"
            query_params: Optional[dict] = {}
            json_body: Optional[dict] = {}
            headers: Optional[dict] = {}
            event_dict: Optional[Dict[str, Any]] = {}
            lambda_context: Optional[Any] = None

            def to_dict(self):
                """
                Returns the request data as a dictionary.
                """
                return {
                    "method": self.method,
                    "query_params": self.query_params,
                    "json_body": self.json_body,
                    "headers": self.headers,
                }

            def to_original_event(self) -> Union[Dict[str, Any], None]:
                """
                Returns the original event dictionary.
                """
                return self.event_dict


        class Response(FastAPIResponse):
            """
            Response class cloned from the selected Response framework super class.
            This class is the one to be imported by the project modules
            """
            body: Union[str, dict]
            status_code: Optional[int] = 200
            headers: Optional[dict] = {}

            def __init__(
                self,
                body: Union[str, dict],
                status_code: Optional[int] = 200,
                headers: Optional[dict] = None
            ):
                """
                Initializes the Response object.
                """
                if isinstance(body, dict):
                    body = json.dumps(body)

                headers = headers if headers else {}
                if 'Content-Type' not in headers:
                    headers['Content-Type'] = 'application/json'
                if 'Access-Control-Allow-Origin' not in headers:
                    headers["Access-Control-Allow-Origin"] = os.environ.get('APP_CORS_ORIGIN', '*')
                if 'Access-Control-Allow-Methods' not in headers:
                    headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                if 'Access-Control-Allow-Headers' not in headers:
                    headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

                if DEBUG:
                    print('FastAPI abstraction' +
                          f'\n| body: {body}' +
                          f'\n| status_code: {status_code}' +
                          f'\n| headers: {headers}')
                super().__init__(
                    content=body,
                    status_code=status_code,
                    headers=headers
                )


        class Blueprint(framework_module.APIRouter):
            """
            Blueprint class cloned from the selected Blueprint framework super class.
            This class is the one to be imported by the project modules
            """


        # FastAPI BlueprintOne implementation

        # JWT

        class AuthTokenPayload(BaseModel):
            """
            Represents the user's payload structure of the JWT token.
            """
            public_id: str


        class AuthorizedRequest(Request):
            """
            Represents the AuthorizedRequest payload structure of the JWT token,
            containing the authenticated user's data.
            """
            user: AuthTokenPayload


        def credentials_exception(
            error_message: Optional[str] = None,
            error_code: Optional[int] = 401,  # Unauthorized
            headers: Optional[dict] = None
        ) -> HTTPException:
            """
            Returns a standard error response
            """
            if not headers:
                headers = {"WWW-Authenticate": "Bearer"}
            if not error_message:
                error_message = 'Could not validate credentials'
            return HTTPException(
                status_code=error_code,
                detail=error_message,
                headers=headers,
            )


        def get_general_authorized_request(
            request: Request
        ) -> Union[AuthorizedRequest, HTTPException]:
            """
            Get the authorized request from the request object.

            Args:
                request (Request): The request object.

            Returns:
                AuthorizedRequest: The authorized request.
            """
            settings = Config()
            if settings.HEADER_TOKEN_ENTRY_NAME not in request.headers:
                # return standard_error_return('A valid token is missing')
                return credentials_exception('A valid token is missing')
            try:
                token_raw = request.headers[settings.HEADER_TOKEN_ENTRY_NAME]
                jwt_token = token_raw.replace('Bearer ', '')
                if DEBUG:
                    log_debug('||| FA REQUEST_AUTHENTICATION' +
                        '\n | HEADER_TOKEN_ENTRY_NAME: ' +
                        f'{settings.HEADER_TOKEN_ENTRY_NAME}' +
                        f'\n | token_raw: {token_raw}' +
                        f'\n | jwt_token: {jwt_token}' +
                        # f'\n | settings.APP_SECRET_KEY: {settings.APP_SECRET_KEY}' +
                        '\n')
                jws_token_data = jwt.decode(
                    jwt_token,
                    settings.APP_SECRET_KEY,
                    algorithms="HS256",
                )
                if DEBUG:
                    log_debug('||| FA REQUEST_AUTHENTICATION' +
                        f' | jws_token_data = {jws_token_data}')

                authorized_request = AuthorizedRequest(
                    # type: ignore[attr-defined]
                    event_dict=request.to_original_event(),
                    # type: ignore[attr-defined]
                    lambda_context=request.lambda_context,
                    # Authentication token data
                    user=jws_token_data,
                )

                if DEBUG:
                    log_debug('||| FA REQUEST_AUTHENTICATION' +
                        f' | authorized_request = {authorized_request}')
            except Exception as err:
                log_error('REQUEST_AUTHENTICATION' +
                    f' | Exception = {str(err)}')
                # return standard_error_return('Token is invalid')
                return credentials_exception('Token is invalid')
            return authorized_request


        # Dependencies

        def build_request(
            method: Optional[str] = None,
            query_params: Optional[dict] = None,
            json_body: Optional[dict] = None,
            headers: Optional[dict] = None,
            preserve_nones: bool = False,
        ) -> Union[Request, AuthorizedRequest]:
            """
            Builds the request query parameters from query_received and cleans it,
            leaving only the ones that are not None

            Args:
                method (str): HTTP method.
                query_params (dict): URL query parameters.
                json_body (dict): Request JSON body.
                headers (dict): Request headers.

            Returns:
                dict: The cleaned request query parameters.
            """
            query_params_reduced = {}
            if query_params:
                # Reduce query_params leaving only the not None items
                query_params_reduced = {k: v for k, v in query_params.items()
                                        if v is not None or preserve_nones}
            headers_reduced = headers if headers else {}
            if "token" in headers_reduced:
                headers_reduced["Authorization"] = f"Bearer {headers_reduced['token']}"
                del headers_reduced["token"]
            if "current_user" in headers_reduced:
                new_request = AuthorizedRequest(
                    method=method if method else "get",
                    query_params=query_params_reduced,
                    json_body=json_body if json_body else {},
                    headers=headers_reduced,
                    user=headers_reduced["current_user"])
            else:
                new_request = Request(
                    method=method if method else "get",
                    query_params=query_params_reduced,
                    json_body=json_body if json_body else {},
                    headers=headers_reduced)
            return new_request


        async def get_current_user(token: str = Depends(oauth2_scheme)):
            """
            Verifies the JWT token and returns the current user.
            """
            request = build_request(headers={"token": token})
            auth_request = get_general_authorized_request(request)
            if not isinstance(auth_request, AuthorizedRequest):
                raise auth_request
            return getattr(auth_request, 'user', None)


        def get_default_fa_request(
            method: Optional[str] = None,
            current_user: Optional[AuthTokenPayload] = None,
            json_body: Optional[dict] = None,
            headers: Optional[dict] = None,
            query_params: Optional[dict] = None,
            preserve_nones: bool = False,
        ) -> Union[Request, AuthorizedRequest]:
            """
            Builds the default FA (FastAPI) Authentication request object.
            """
            params = {
                "method": method or 'get',
                "json_body": json_body if json_body else {},
                "headers": headers if headers else {},
                "query_params": query_params if query_params else {},
                "preserve_nones": preserve_nones,
            }
            if current_user:
                params["headers"]["current_user"] = current_user
            request = build_request(**params)
            return request


        class BlueprintOne(APIRouter):
            """
            Class to register a new route with optional schema validation and authorization.
            """
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.request = None
                self.other_params = None

            def get_current_app(self):
                """
                Get the current App object. It must be called inside a router function.
                """
                return self

            def get_current_request(self):
                """
                Get the current App object. It must be called inside a router function.
                """
                return self.request

            def get_other_params(self):
                """
                Get the other_params object.
                """
                return self.other_params

            def api_route(
                self,
                path: str,
                methods: Union[str, List[str]],
                requires_auth: Optional[bool] = True,
                preserve_nones: Optional[bool] = False,
                other_params: Optional[dict] = None,
                **kwargs
            ):
                def decorator(func: Callable):
                    async def endpoint_wrapper(request: Request, *args, **kwargs):
                        current_user = None
                        if requires_auth:
                            current_user = await get_current_user()

                        json_body = await request.json() \
                            if request.method in ["POST", "PUT", "PATCH"] \
                            else None
                        headers = dict(request.headers)
                        query_params = dict(request.query_params)

                        request_obj = get_default_fa_request(
                            method=request.method,
                            current_user=current_user,
                            json_body=json_body,
                            headers=headers,
                            query_params=query_params,
                            preserve_nones=preserve_nones,
                        )
                        self.request = request_obj
                        self.other_params = other_params or {}

                        return await func(request, *args, **kwargs)

                    self.add_api_route(
                        path=path,
                        endpoint=endpoint_wrapper,
                        methods=methods,
                        include_in_schema=True,
                        **kwargs
                    )
                    return endpoint_wrapper

                return decorator

            def get(
                self,
                path: str,
                requires_auth: Optional[bool] = True,
                preserve_nones: Optional[bool] = False,
                other_params: Optional[dict] = None,
                **kwargs
            ):
                return self.api_route(
                    path,
                    methods=["GET"],
                    requires_auth=requires_auth,
                    preserve_nones=preserve_nones,
                    other_params=other_params,
                    **kwargs
                )

            def post(
                self,
                path: str,
                requires_auth: Optional[bool] = True,
                preserve_nones: Optional[bool] = False,
                other_params: Optional[dict] = None,
                **kwargs
            ):
                return self.api_route(
                    path,
                    methods=["POST"],
                    requires_auth=requires_auth,
                    preserve_nones=preserve_nones,
                    other_params=other_params,
                    **kwargs
                )

            def put(
                self,
                path: str,
                requires_auth: Optional[bool] = True,
                preserve_nones: Optional[bool] = False,
                other_params: Optional[dict] = None,
                **kwargs
            ):
                return self.api_route(
                    path,
                    methods=["PUT"],
                    requires_auth=requires_auth,
                    preserve_nones=preserve_nones,
                    other_params=other_params,
                    **kwargs
                )

            def delete(
                self,
                path: str,
                requires_auth: Optional[bool] = True,
                preserve_nones: Optional[bool] = False,
                other_params: Optional[dict] = None,
                **kwargs
            ):
                return self.api_route(
                    path,
                    methods=["DELETE"],
                    requires_auth=requires_auth,
                    preserve_nones=preserve_nones,
                    other_params=other_params,
                    **kwargs
                )


    except ImportError as frm_err:
        raise ImportError(f"Unable to import '{FRAMEWORK}': {frm_err}") from None
