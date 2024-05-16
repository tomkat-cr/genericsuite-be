"""
FastAPI abstraction layer
"""
from typing import Optional, Union, Dict, Any

import os
import importlib
import json

# from fastapi import HTTPException
# from fastapi import Request as FastAPIRequest
# from fastapi import Blueprint as FastAPIBlueprint
from fastapi import Response as FastAPIResponse
from pydantic import BaseModel

from genericsuite.fastapilib.util.blueprint_one import (
    BlueprintOne as FaBlueprintOne
)

DEBUG = False

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

        class BlueprintOne(FaBlueprintOne):
            """
            Class to register a new route with optional schema validation and authorization.
            """

    except ImportError as err:
        raise ImportError(f"Unable to import '{FRAMEWORK}': {err}") from None
