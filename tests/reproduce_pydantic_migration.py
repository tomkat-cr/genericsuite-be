
from unittest.mock import MagicMock
from pydantic import BaseModel
from genericsuite.util.schema_utilities import schema_verification

# Define a test Pydantic model


class TestModel(BaseModel):
    name: str
    age: int


def test_schema_verification_success():
    print("Testing schema_verification success...")
    data = {"name": "Test User", "age": 30}
    logger = MagicMock()

    result = schema_verification(data, TestModel, logger)

    if result == data:
        print("SUCCESS: Valid data passed verification.")
    else:
        print(f"FAILURE: Expected {data}, but got {result}")
        exit(1)
    logger.error.assert_not_called()


def test_schema_verification_failure():
    print("Testing schema_verification failure...")
    data = {"name": "Test User", "age": "invalid"}
    logger = MagicMock()

    result = schema_verification(data, TestModel, logger)

    if result is None:
        print("SUCCESS: Invalid data failed verification and logged error.")
    else:
        print(f"FAILURE: Expected None, but got {result}")
        exit(1)
    logger.error.assert_called_once()


if __name__ == "__main__":
    try:
        test_schema_verification_success()
        test_schema_verification_failure()
        print("\nALL TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
