from genericsuite.util.app_logger import sanitize_log_message
import sys
import os
from unittest.mock import MagicMock

# Mock bson before importing utilities to avoid ModuleNotFoundError
sys.modules["bson"] = MagicMock()
sys.modules["bson.json_util"] = MagicMock()

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Import the function after path setup and mocking


def test_sanitization():
    print("Testing log sanitization...")

    # Test case 1: Message with newline
    msg1 = "User logged in\nAdmin: YES"
    sanitized1 = sanitize_log_message(msg1)
    print(f"Original 1: {repr(msg1)}")
    print(f"Sanitized 1: {repr(sanitized1)}")
    assert sanitized1 == "User logged in\\nAdmin: YES"

    # Test case 2: Message with carriage return
    msg2 = "Attack payload\rCRITICAL"
    sanitized2 = sanitize_log_message(msg2)
    print(f"Original 2: {repr(msg2)}")
    print(f"Sanitized 2: {repr(sanitized2)}")
    assert sanitized2 == "Attack payload\\rCRITICAL"

    # Test case 3: Message with both
    msg3 = "Line 1\r\nLine 2"
    sanitized3 = sanitize_log_message(msg3)
    print(f"Original 3: {repr(msg3)}")
    print(f"Sanitized 3: {repr(sanitized3)}")
    assert sanitized3 == "Line 1\\r\\nLine 2"

    # Test case 4: None message
    msg4 = None
    sanitized4 = sanitize_log_message(msg4)
    print(f"Original 4: {repr(msg4)}")
    print(f"Sanitized 4: {repr(sanitized4)}")
    assert sanitized4 == ""

    # Test case 5: Int message
    msg5 = 123
    sanitized5 = sanitize_log_message(msg5)
    print(f"Original 5: {repr(msg5)}")
    print(f"Sanitized 5: {repr(sanitized5)}")
    assert sanitized5 == "123"

    print("All tests passed!")


if __name__ == "__main__":
    test_sanitization()
