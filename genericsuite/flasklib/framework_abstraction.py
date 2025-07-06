
"""
Flask abstraction layer
"""
from typing import Optional, Union, Dict, Any
import os
import importlib
import json

from pydantic import BaseModel

# https://stackoverflow.com/questions/47277374/flask-get-current-blueprint-webroot
from flask import (
    Blueprint as FlaskBlueprint,
    Response as FlaskResponse,
    request,
)

DEBUG = False

FRAMEWORK_LOADED = False
FRAMEWORK = os.environ.get('CURRENT_FRAMEWORK', '').lower()
if FRAMEWORK == 'flask':
    try:
        framework_module = importlib.import_module(FRAMEWORK)
        FRAMEWORK_LOADED = True
        _ = DEBUG and \
            print(f'Flask abstraction | framework_module: {framework_module}')

        class FrameworkClass(framework_module.Flask):
            """
            Framkework class cloned from the selected framework super class.
            """

        class Request(BaseModel):
            """
            Request class cloned from the selected Request framework super
            class.
            This class is the one to be imported by the project modules
            """
            method: Optional[str] = "GET"
            query_params: Optional[dict] = {}
            json_body: Optional[dict] = {}
            headers: Optional[dict] = {}
            event_dict: Optional[Dict[str, Any]] = {}
            lambda_context: Optional[Any] = None
            context: Optional[dict] = {}

            def set_properties(self):
                # https://tedboy.github.io/flask/generated/generated/flask.Request.html
                self.method = request.method
                # self.query_params = request.args.to_dict()
                self.query_params = dict(request.args)
                # self.json_body = request.form.to_dict()
                self.json_body = request.get_json(silent=True)
                self.headers = dict(request.headers)
                # https://tedboy.github.io/flask/interface_api.incoming_request_data.html#flask.Request.full_path
                # https://stackoverflow.com/questions/62147474/how-to-print-complete-http-request-using-chalice
                self.context = {
                    "resourcePath": request.path.split('/')[-1],
                    "Path": (request.script_root if hasattr(request,
                             'script_root') else '') + request.path,
                    "requestId": request.headers.get('X-Amzn-Trace-Id'),
                    "apiId": request.headers.get('X-Api-Id'),
                    "resourceId": request.headers.get('X-Amz-Api-Id'),
                }
                _ = DEBUG and print(
                    'Flask abstraction | Request:'
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

        class Response(FlaskResponse):
            """
            Response class cloned from the selected Response framework super
            class with added functionality to handle request context.
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
                    headers["Access-Control-Allow-Origin"] = \
                        os.environ.get('APP_CORS_ORIGIN', '*')
                if 'Access-Control-Allow-Methods' not in headers:
                    headers["Access-Control-Allow-Methods"] = \
                        "GET, POST, PUT, DELETE, OPTIONS"
                if 'Access-Control-Allow-Headers' not in headers:
                    headers["Access-Control-Allow-Headers"] = \
                        "Content-Type, Authorization"

                _ = DEBUG and print(
                    'Flask abstraction | Response:'
                    f'\n| body: {body}'
                    f'\n| status_code: {status_code}'
                    f'\n| headers: {headers}')

                # Covert headers to a list of ``(key, value)`` tuples,
                # which is what Flask expects
                headers_for_flask = []
                for key, value in headers.items():
                    headers_for_flask.append((key, value))
                super().__init__(response=body, status=status_code,
                                 headers=headers_for_flask)

        # class Blueprint(framework_module.Blueprint):
        class Blueprint(FlaskBlueprint):
            """
            Blueprint class cloned from the selected Blueprint framework super
            class.
            This class is the one to be imported by the project modules
            """

        # class BlueprintOne(FlaskBlueprintOne):
        class BlueprintOne(Blueprint):
            """
            Class to register a new route with optional schema validation and
            authorization.
            """

    except ImportError as err:
        raise ImportError(f"Unable to import '{FRAMEWORK}': {err}") from None
