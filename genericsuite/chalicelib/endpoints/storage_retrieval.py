"""
Storage retrieval for Chalice
"""
from typing import Union, Optional

# from chalice.app import Request, Response
# from genericsuite.util.blueprint_one import BlueprintOne
from genericsuite.util.framework_abs_layer import Request, Response, BlueprintOne
from genericsuite.util.app_logger import log_debug

from genericsuite.util.aws import storage_retieval
from genericsuite.util.utilities import (
    return_resultset_jsonified_or_exception,
)

DEBUG = True
bp = BlueprintOne(__name__)


def debug_args(args1, kwargs1):
    """ Debug args """
    if DEBUG:
        log_debug(f"args1: {args1}")
        log_debug(f"kwargs1: {kwargs1}")


@bp.route('/', methods=['GET'])
def storage_retrieval_no_item_id_endpoint(
    *args,
    **kwargs,
) -> Response:
    """ Get file from ecrypted URL """
    debug_args(args, kwargs)
    request = bp.get_current_request()  #   bp.current_app.current_request
    # Report the error ASR-E1010
    item_id = None
    other_params = kwargs.get('other_params', {}) or {}
    other_params['response_type'] = other_params.get('response_type') or "streaming"
    return storage_retieval_chalice(request=request, blueprint=bp,
        item_id=item_id, other_params=other_params)


@bp.route('/{item_id}', methods=['GET'])
def storage_retrieval_endpoint(
    # item_id: str,
    *args,
    **kwargs,
) -> Response:
    """ Get file from ecrypted URL """
    debug_args(args, kwargs)
    request = bp.get_current_request()  #   bp.current_app.current_request
    item_id = kwargs.get('item_id')
    other_params = kwargs.get('other_params', {}) or {}
    other_params['response_type'] = other_params.get('response_type') or "streaming"
    return storage_retieval_chalice(request=request, blueprint=bp,
        item_id=item_id, other_params=other_params)


@bp.route('/{item_id}/{response_type}', methods=['GET'])
def storage_retrieval_with_response_type_endpoint(
    # other_params: Optional[Union[dict, None]] = None,
    # item_id: str,
    # response_type: str,
    *args, **kwargs,
) -> Response:
    """ Get file from ecrypted URL """
    request = bp.get_current_request()  #   bp.current_app.current_request
    item_id = kwargs.get('item_id')
    other_params = kwargs.get('other_params', {}) or {}
    other_params['response_type'] = kwargs.get('response_type') or "streaming"
    return storage_retieval_chalice(request=request, blueprint=bp,
        item_id=item_id, other_params=other_params)


def storage_retieval_chalice(
    request: Request,
    blueprint: BlueprintOne,
    item_id: str,
    other_params: Optional[Union[dict, None]] = None,
) -> Response:
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
    # resultset = storage_retieval(request, item_id, other_params)
    resultset = storage_retieval(request=request, blueprint=blueprint,
        item_id=item_id, other_params=other_params)
    if resultset.get('error'):
        return return_resultset_jsonified_or_exception(
            resultset
        )
    if other_params.get('response_type') == "streaming":
        # Return the file content as a Streaming Response
        return Response(
            body=resultset['content'],
            status_code=200,
            headers={'Content-Type': 'application/octet-stream'}
        )
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
