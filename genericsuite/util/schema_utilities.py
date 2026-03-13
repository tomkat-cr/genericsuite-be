"""
Schema utilities
"""
from typing import Union, Type
from logging import Logger
from pydantic import BaseModel, ValidationError


def schema_verification(
    json_body: dict,
    schema_validator: Type[BaseModel],
    app_logger: Logger,
) -> Union[dict, None]:
    """
    Validate the input data against the provided schema.

    Args:
        json_body (dict): The input data to be validated.
        schema (BaseModel): The schema to validate input data.
        app_logger (Logger): The logger to log validation errors.

    Returns:
        Union[dict, None]: The validated data or None if the input data
            does not conform to the schema.
    """
    try:
        # Pydantic v2 usage
        return schema_validator.model_validate(json_body).model_dump()
    except ValidationError as error:
        app_logger.error(f'Query error: {error.errors()}')
    return None
