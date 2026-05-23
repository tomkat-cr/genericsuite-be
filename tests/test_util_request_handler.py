"""
Tests for genericsuite/util/request_handler.py — RequestHandler class.
"""
import sys

# Delete any cached mock (test_db_abstractor_factory mocks this at module level)
for _mod in list(sys.modules):
    if "genericsuite.util.request_handler" == _mod:
        del sys.modules[_mod]

from genericsuite.util.request_handler import RequestHandler


def test_request_handler_initial_state():
    rh = RequestHandler()
    assert rh.get_request() is None


def test_request_handler_set_and_get():
    rh = RequestHandler()
    fake_request = object()
    rh.set_request(fake_request)
    assert rh.get_request() is fake_request


def test_request_handler_overwrite():
    rh = RequestHandler()
    rh.set_request("first")
    rh.set_request("second")
    assert rh.get_request() == "second"


def test_request_handler_set_none():
    rh = RequestHandler()
    rh.set_request("something")
    rh.set_request(None)
    assert rh.get_request() is None
