import yaml
import json

from fastapi import Request, Response, FastAPI

from genericsuite.fastapilib.util.blueprint_one import BlueprintOne

DEBUG = False

router = BlueprintOne()


@router.get(
    "/yaml",
    response_class=Response,
    include_in_schema=False
)
async def get_openapi_yaml(request: Request):
    app = request.app
    openapi_spec = app.openapi()
    openapi_yaml = yaml.dump(openapi_spec, default_flow_style=False)
    headers = {
        'Content-Disposition':
        f'attachment; filename="{app.title}_openapi.yaml"'
    }
    return Response(
        content=openapi_yaml,
        media_type="application/x-yaml",
        headers=headers,
    )


@router.get(
    "/json",
    response_class=Response,
    include_in_schema=False
)
async def get_openapi_json(request: Request):
    app = request.app
    openapi_data = app.openapi()
    headers = {
        'Content-Disposition':
        f'attachment; filename="{app.title}_openapi.json"'
    }
    return Response(
        content=json.dumps(openapi_data),
        media_type="application/json",
        headers=headers,
    )


def save_openapi_json(app: FastAPI, file_path: str):
    """
    Save the OpenAPI JSON to a file
    """
    openapi_data = app.openapi()
    with open(file_path, "w") as file:
        json.dump(openapi_data, file, indent=2)


def save_openapi_yaml(app: FastAPI, file_path: str):
    """
    Save the OpenAPI YAML to a file
    """
    openapi_data = app.openapi()
    with open(file_path, "w") as file:
        yaml.dump(openapi_data, file, default_flow_style=False)
