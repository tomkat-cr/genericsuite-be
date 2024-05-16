"""
Schema utilities
"""
from typing import Union
from logging import Logger
from marshmallow import Schema, ValidationError


def schema_verification(
    json_body: dict,
    schema_validator: Schema,
    app_logger: Logger,
) -> Union[dict, None]:
    """
    Validate the input data against the provided schema.

    Args:
        json_body (dict): The input data to be validated.
        schema (Schema): The schema to validate input data.
        app_logger (Logger): The logger to log validation errors.

    Returns:
        Union[dict, None]: The validated data or None if the input data
            does not conform to the schema.
    """
    try:
        return schema_validator.load(json_body)
    except ValidationError as error:
        app_logger.error(f'Query error: {error.messages}')
    return None
