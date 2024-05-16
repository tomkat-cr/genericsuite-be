"""
Storage retrieval for FastAPI
"""
from typing import Union, Optional
from typing import Any
import io

# from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from genericsuite.util.framework_abs_layer import Request, Response
from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
from genericsuite.fastapilib.util.dependencies import (
    get_default_fa_request,
)
from genericsuite.util.aws import storage_retieval
from genericsuite.util.utilities import (
    return_resultset_jsonified_or_exception,
)

# router = APIRouter()
router = BlueprintOne()


@router.get('/')
async def storage_retrieval_no_item_id_endpoint(
) -> Any:
    """ Get authorized menu options """
    request, other_params = get_default_fa_request()
    # Report the error ASR-E1010
    item_id = None
    return storage_retieval_fa(request=request, blueprint=router,
        item_id=item_id, other_params=other_params)


@router.get('/{item_id}')
async def storage_retrieval_endpoint(
    item_id: str,
) -> Any:
    """ Get authorized menu options """
    request, other_params = get_default_fa_request()
    other_params['response_type'] = other_params.get('response_type') or "streaming"
    return storage_retieval_fa(request=request, blueprint=router,
        item_id=item_id, other_params=other_params)


@router.get('/{item_id}/{response_type}')
async def storage_retrieval_with_response_type_endpoint(
    # It's optional to eventually report the error ASR-E1010
    item_id: str,
    response_type: str,
) -> Any:
    """ Get authorized menu options """
    request, other_params = get_default_fa_request()
    other_params['response_type'] = response_type or "streaming"
    return storage_retieval_fa(request=request, blueprint=router,
        item_id=item_id, other_params=other_params)


def storage_retieval_fa(
    request: Request,
    blueprint: BlueprintOne,
    item_id: Union[str, None],
    other_params: Optional[Union[dict, None]] = None,
) -> Union[Response, StreamingResponse]:
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
    other_params = other_params or {}
    resultset = storage_retieval(request=request, blueprint=blueprint,
        item_id=item_id, other_params=other_params)
    if resultset.get('error'):
        return return_resultset_jsonified_or_exception(
            resultset
        )

    if other_params.get('response_type') == "streaming":
        # Return the file content as a Streaming Response
        return StreamingResponse(io.BytesIO(resultset['content']),
            media_type=resultset['mime_type'])

    # Return the file content as a normal Response
    headers = {
        'Content-Type': resultset['mime_type'],
        'Content-Disposition': 'attachment; filename=' \
            f'"{resultset["filename"]}"',
    }
    return Response(
        body=resultset['content'],
        status_code=200,
        headers=headers
    )
