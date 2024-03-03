"""
Generic Endpoint builder for FastAPI
"""
from fastapi import FastAPI
from pydantic import BaseModel
import json


# app = FastAPI()

class Endpoint(BaseModel):
    name: str
    route: str
    method: str
    response_model: str


def generate_endpoints_from_json(app: FastAPI, json_file: str) -> None:
    with open(json_file) as f:
        endpoints = json.load(f)
    for endpoint in endpoints:
        endpoint_obj = Endpoint(**endpoint)
        # Assuming the response model is a Pydantic model and already imported
        response_model = globals()[endpoint_obj.response_model]
        if endpoint_obj.method.lower() == 'get':
            app.get(endpoint_obj.route, response_model=response_model)(
                create_endpoint_function(endpoint_obj.name)
            )
        elif endpoint_obj.method.lower() == 'post':
            app.post(endpoint_obj.route, response_model=response_model)(
                create_endpoint_function(endpoint_obj.name)
            )
        # Add other HTTP methods as needed


def create_endpoint_function(name: str) -> callable:
    def endpoint_function():
        # Placeholder function logic
        return {"message": f"This is the {name} endpoint"}
    return endpoint_function

# Example usage:
# generate_endpoints_from_json(app, 'endpoints.json')
