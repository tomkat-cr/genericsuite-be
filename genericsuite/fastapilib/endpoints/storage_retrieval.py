"""
Storage retrieval for FastAPI
"""
from typing import Union, Optional
from typing import Any
import os
import io

from fastapi import Request as FaRequest
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse

from genericsuite.util.framework_abs_layer import Request, Response
from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
from genericsuite.fastapilib.util.dependencies import (
    get_default_fa_request,
)
from genericsuite.util.aws import storage_retieval
from genericsuite.util.app_logger import log_debug
from genericsuite.util.utilities import (
    return_resultset_jsonified_or_exception,
    send_file_text_text,
)
# from genericsuite.config.config import Config

DEBUG = True

DEFAULT_DOWNLOAD_METHOD = "fastapi"
# DEFAULT_DOWNLOAD_METHOD = "inline"
# DEFAULT_DOWNLOAD_METHOD = "streaming"
# DEFAULT_DOWNLOAD_METHOD = "attachment"

# router = APIRouter()
router = BlueprintOne()


@router.get('/')
async def storage_retrieval_no_item_id_endpoint(
    request: FaRequest,
    background_tasks: BackgroundTasks,
) -> Any:
    """ Get authorized menu options """
    gs_request, other_params = get_default_fa_request()
    router.set_current_request(request, gs_request)
    # Report the error ASR-E1010
    item_id = None
    return storage_retieval_fa(request=gs_request, blueprint=router,
        item_id=item_id, other_params=other_params,
        background_tasks=background_tasks)

# Why these endpoint definitions return type is "-> Any": and not:
# "-> Union[Response, FileResponse, StreamingResponse]":
#
# Because this error:
#
# fastapi.exceptions.FastAPIError: Invalid args for response field! Hint: check
# that typing.Union[genericsuite.util.framework_abs_layer.Response,
# starlette.responses.FileResponse, starlette.responses.StreamingResponse] is a
# valid Pydantic field type. If you are using a return type annotation that is
# not a valid Pydantic field (e.g. Union[Response, dict, None]) you can disable
# generating the response model from the type annotation with the path operation
# decorator parameter response_model=None.
#
# Read more: https://fastapi.tiangolo.com/tutorial/response-model/


@router.get('/{item_id}')
async def storage_retrieval_endpoint(
    request: FaRequest,
    item_id: str,
    background_tasks: BackgroundTasks,
) -> Any:
    """ Get authorized menu options """
    gs_request, other_params = get_default_fa_request()
    router.set_current_request(request, gs_request)
    other_params['response_type'] = other_params.get('response_type') or DEFAULT_DOWNLOAD_METHOD
    return storage_retieval_fa(request=gs_request, blueprint=router,
        item_id=item_id, other_params=other_params,
        background_tasks=background_tasks)


@router.get('/{item_id}/{response_type}')
async def storage_retrieval_with_response_type_endpoint(
    request: FaRequest,
    # It's optional to eventually report the error ASR-E1010
    item_id: str,
    response_type: str,
    background_tasks: BackgroundTasks,
) -> Any:
    """ Get authorized menu options """
    gs_request, other_params = get_default_fa_request()
    router.set_current_request(request, gs_request)
    other_params['response_type'] = response_type or DEFAULT_DOWNLOAD_METHOD
    return storage_retieval_fa(request=gs_request, blueprint=router,
        item_id=item_id, other_params=other_params,
        background_tasks=background_tasks)


def remove_temp_file(file_path: str) -> None:
    """ Remove the temp file """
    _ = DEBUG and log_debug(f"Removing temp file: {file_path}")
    os.remove(file_path)


def storage_retieval_fa(
    request: Request,
    blueprint: BlueprintOne,
    item_id: Union[str, None],
    other_params: Optional[Union[dict, None]] = None,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Union[Response, FileResponse, StreamingResponse]:
    """
    Get S3 bucket content from encrypted item_id
    Args:
        request (Request): The request object.
        other_params (dict, optional): Other parameters. Defaults to None.
        item_id (str, optional): The item_id with the encrypted elements
            (bucket_name, separator and key). Defaults to None.
    Returns:
        Union[Response, StreamingResponse]: The object as streaming response
            or error response.
    """
    # settings = Config()
    other_params = other_params or {}

    if not other_params.get('response_type'):
        other_params['response_type'] = "fastapi"

    if other_params.get('response_type') in ["fastapi", "gs"]:
        other_params['mode'] = 'download'
    else:
        other_params['mode'] = 'get'

    resultset = storage_retieval(request=request, blueprint=blueprint,
        item_id=item_id, other_params=other_params)
    if resultset.get('error'):
        return return_resultset_jsonified_or_exception(
            resultset
        )

    if other_params.get('response_type') in ["fastapi", "gs"]:
        file_path = resultset['local_file_path']
        background_tasks.add_task(remove_temp_file, file_path=file_path)
        _ = DEBUG and log_debug(f"Temp file read | file_path: {file_path}")

    if other_params.get('response_type') == "gs":
        # Return the file content as GenericSuite way
        # (the one that worked for audio file and the ai_chatbot)
        _ = DEBUG and log_debug("Returning file content the Genericsuite way")
        return send_file_text_text(file_path)

    if other_params.get('response_type') == "fastapi":
        # Return the file content the standard FastAPI way
        # https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse
        _ = DEBUG and log_debug("Returning file content as FileResponse")
        # return FileResponse(file_path, media_type=resultset['mime_type'])
        return FileResponse(file_path)

    if other_params.get('response_type') == "streaming":
        # Return the file content as a Streaming Response
        _ = DEBUG and log_debug("Returning file content as StreamingResponse")
        return StreamingResponse(io.BytesIO(resultset['content']),
            media_type=resultset['mime_type'])

    content_disposition_method = "inline"
    if other_params.get('response_type') == "attachment":
        content_disposition_method = "inline"

    # Return the file content as a normal Response
    headers = {
        'Content-Type': resultset['mime_type'],
        'Content-Disposition': f'{content_disposition_method}; filename=' \
            f'"{resultset["filename"]}"',
    }
    _ = DEBUG and log_debug("Returning file content as Response" +
        f' | headers: {headers}')
    return Response(
        body=resultset['content'],
        status_code=200,
        headers=headers
    )
