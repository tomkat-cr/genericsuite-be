"""
Tests for genericsuite/util/exceptions.py — custom exception hierarchy.

The exceptions.py file currently contains only commented-out code; this test
confirms the module is importable and that standard Python exceptions work.
"""


def test_module_imports_without_error():
    """exceptions.py is importable regardless of its content."""
    import genericsuite.util.exceptions as exc_mod
    assert exc_mod is not None


def test_standard_exception_can_be_raised_and_caught():
    """Standard Python exceptions work in this test environment."""
    try:
        raise ValueError("test error")
    except Exception as e:
        assert "test error" in str(e)


def test_custom_exception_inherits_from_base():
    """A project-style custom exception can be caught as Exception."""
    class GenericSuiteError(Exception):
        def __init__(self, msg: str):
            self.msg = msg
            super().__init__(msg)

    try:
        raise GenericSuiteError("something broke")
    except Exception as e:
        assert "something broke" in str(e)


def test_custom_exception_stores_message():
    class GenericSuiteError(Exception):
        def __init__(self, msg: str):
            self.msg = msg
            super().__init__(msg)

    err = GenericSuiteError("stored message")
    assert err.msg == "stored message"
