
"""
MCP abstraction layer
"""
from typing import Optional, Union, Dict, Any, Callable, List
import os
import importlib
import json

from pydantic import BaseModel

# MCP and FastMCP imports
from fastmcp import FastMCP

DEBUG = False

FRAMEWORK_LOADED = False
FRAMEWORK = os.environ.get('CURRENT_FRAMEWORK', '').lower()
if FRAMEWORK == 'mcp':
    try:
        framework_module = importlib.import_module('fastmcp')
        FRAMEWORK_LOADED = True
        _ = DEBUG and \
            print(f'MCP abstraction | framework_module: {framework_module}')

        class FrameworkClass(BaseModel):
            """
            Framkework class cloned from the selected framework super class.
            """

        class Request(BaseModel):
            """
            Request class cloned from the selected Request framework super
            class.
            This class is the one to be imported by the project modules
            """
            _method: Optional[str] = "GET"
            _query_params: Optional[dict] = {}
            _json_body: Optional[dict] = {}
            _headers: Optional[dict] = {}
            _event_dict: Optional[Dict[str, Any]] = {}
            _lambda_context: Optional[Any] = None
            _context: Optional[dict] = {}

            @property
            def method(self):
                return self._method

            @property
            def query_params(self):
                return self._query_params

            @property
            def json_body(self):
                return self._json_body

            @property
            def headers(self):
                return self._headers

            @property
            def event_dict(self):
                return self._event_dict

            @property
            def lambda_context(self):
                return self._lambda_context

            @property
            def context(self):
                return self._context

            @method.setter
            def method(self, method: Optional[str]):
                self._method = method

            @query_params.setter
            def query_params(self, query_params: Optional[dict]):
                self._query_params = query_params

            @json_body.setter
            def json_body(self, json_body: Optional[dict]):
                self._json_body = json_body

            @headers.setter
            def headers(self, headers: Optional[dict]):
                self._headers = headers

            @event_dict.setter
            def event_dict(self, event_dict: Optional[Dict[str, Any]]):
                self._event_dict = event_dict

            @lambda_context.setter
            def lambda_context(self, lambda_context: Optional[Any]):
                self._lambda_context = lambda_context

            @context.setter
            def context(self, context: Optional[dict]):
                self._context = context

            def set_properties(self):
                # self.method = request.method
                # self.query_params = dict(request.args)
                # self.json_body = request.get_json(silent=True)
                # self.headers = dict(request.headers)
                self.context = {
                    "resourcePath": '',
                    "Path": '',
                    "requestId": None,
                    "apiId": None,
                    "resourceId": None,
                }
                _ = DEBUG and print(
                    'MCP abstraction | Request:'
                    f'\n | self.query_params: {self.query_params}'
                    f'\n | self.json_body: {self.json_body}'
                    f'\n | self.headers: {self.headers}'
                    f'\n | self.context: {self.context}'
                )

            def to_dict(self):
                """
                Returns the request data as a dictionary.
                """
                return {
                    "method": self.method,
                    "query_params": self.query_params,
                    "json_body": self.json_body,
                    "headers": self.headers,
                    "context": self.context,
                }

            def to_original_event(self) -> Union[Dict[str, Any], None]:
                """
                Returns the original event dictionary.
                """
                return self.event_dict

        class Response(BaseModel):
            """
            Response class cloned from the selected Response framework super
            class with added functionality to handle request context.
            This class is the one to be imported by the project modules
            """
            _body: Union[str, dict]
            _status_code: Optional[int] = 200
            _headers: Optional[dict] = {}

            @property
            def body(self):
                return self._body

            @property
            def status_code(self):
                return self._status_code

            @property
            def headers(self):
                return self._headers

            @body.setter
            def body(self, body: Union[str, dict]):
                self._body = body

            @status_code.setter
            def status_code(self, status_code: Optional[int]):
                self._status_code = status_code

            @headers.setter
            def headers(self, headers: Optional[dict]):
                self._headers = headers

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
                    headers["Access-Control-Allow-Origin"] = \
                        os.environ.get('APP_CORS_ORIGIN', '*')
                if 'Access-Control-Allow-Methods' not in headers:
                    headers["Access-Control-Allow-Methods"] = \
                        "GET, POST, PUT, DELETE, OPTIONS"
                if 'Access-Control-Allow-Headers' not in headers:
                    headers["Access-Control-Allow-Headers"] = \
                        "Content-Type, Authorization"

                self.body = body
                self.status_code = status_code
                self.headers = headers

                _ = DEBUG and print(
                    'MCP abstraction | Response:'
                    f'\n| body: {body}'
                    f'\n| status_code: {status_code}'
                    f'\n| headers: {headers}')

            def to_dict(self):
                """
                Returns the response data as a dictionary.
                """
                return {
                    "body": self.body,
                    "status_code": self.status_code,
                    "headers": self.headers,
                }

        class Blueprint(BaseModel):
            """
            Blueprint class cloned from the selected Blueprint framework super
            class.
            This class is the one to be imported by the project modules
            """
            _name: str = "NoName"
            _current_app: Optional[Any] = None
            _current_request: Optional[Any] = None
            _context: Optional[dict] = {}
            _event_dict: Optional[dict] = {}
            _routes: Optional[list] = []

            @property
            def name(self):
                return self._name

            @property
            def current_app(self):
                return self._current_app

            @property
            def current_request(self):
                return self._current_request

            @property
            def context(self):
                return self._context

            @property
            def event_dict(self):
                return self._event_dict

            @property
            def routes(self):
                return self._routes

            @name.setter
            def name(self, name: str) -> None:
                """
                Set the name of the blueprint.
                """
                self._name = name

            @current_app.setter
            def current_app(self, current_app: Any) -> None:
                """
                Set the current App object.
                """
                self._current_app = current_app

            @current_request.setter
            def current_request(self, current_request: Any) -> None:
                """
                Set the current request object.
                """
                self._current_request = current_request

            @context.setter
            def context(self, context: dict) -> None:
                """
                Set the context of the blueprint.
                """
                self._context = context

            @event_dict.setter
            def event_dict(self, event_dict: dict) -> None:
                """
                Set the event dictionary of the blueprint.
                """
                self._event_dict = event_dict

            @routes.setter
            def routes(self, routes: list) -> None:
                """
                Set the routes of the blueprint.
                """
                self._routes = routes

            def __init__(self, *args, **kwargs):
                """
                Initialize the Blueprint class.
                """
                if len(args) > 0:
                    self.name = args[0]
                if len(args) > 1:
                    self.current_app = args[1]
                if len(args) > 2:
                    self.current_request = args[2]
                if len(args) > 3:
                    self.context = args[3]
                if len(args) > 4:
                    self.event_dict = args[4]

            def get_current_app(self) -> Any:
                """
                Get the current App object. It must be called inside a router
                function.
                """
                return self.current_app

            def set_current_app(self, mcp: FastMCP) -> FastMCP:
                """
                Set the current App object. It must be called inside a router
                function.
                """
                self.current_app = mcp
                return self.current_app

            def get_current_request(self) -> Any:
                """
                Get the current request object. It must be called inside a
                router function.
                """
                return self.current_request

            def set_current_request(self, mcp_request: Request) -> Any:
                """
                Set the current request object. It must be called inside a
                router function.
                """
                self.current_request = mcp_request
                self.context = {
                    "resourcePath": mcp_request.url.path.split('/')[-1]
                    if hasattr(mcp_request, 'url') else '',
                    "Path": str(mcp_request.url.path)
                    if hasattr(mcp_request, 'url') else '',
                    "requestId": mcp_request.headers.get('X-Amzn-Trace-Id')
                    if hasattr(mcp_request, 'headers') else '',
                    "apiId": mcp_request.headers.get('X-Api-Id')
                    if hasattr(mcp_request, 'headers') else '',
                    "resourceId": mcp_request.headers.get('X-Amz-Api-Id')
                    if hasattr(mcp_request, 'headers') else '',
                }
                return self.current_request

            def to_dict(self):
                """
                Returns the request data as a dictionary.
                """
                return {
                    "name": self.name,
                    "current_app": self.current_app,
                    "current_request": self.current_request,
                    "context": self.context,
                }

            def to_original_event(self) -> Union[Dict[str, Any], None]:
                """
                Returns the original event dictionary.
                """
                return self.event_dict

            def route(
                self,
                path: str,
                authorizor: Callable = None,
                methods: List[str] = ['GET'],
                other_params: Dict[str, Any] = {},
            ):
                """
                Route a new endpoint.
                """
                self.routes.append({
                    "path": path,
                    "authorizor": authorizor,
                    "methods": methods,
                    "other_params": other_params,
                })
                return self

        class BlueprintOne(Blueprint):
            """
            Class to register a new route with optional schema validation and
            authorization.
            """

    except ImportError as err:
        raise ImportError(f"Unable to import '{FRAMEWORK}': {err}") from None
