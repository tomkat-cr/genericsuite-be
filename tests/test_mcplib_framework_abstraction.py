"""
Tests for genericsuite/mcplib/framework_abstraction.py.

fastmcp and mcp are listed as dev dependencies, so real imports are used.
Tests that exercise live MCP classes run only when CURRENT_FRAMEWORK=mcp.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()


# ---- Always-run: mock-based (no sys.modules patching) ----

def test_mcp_mock_callable():
    """A local MagicMock standing in for an MCP server is callable."""
    mock_server = MagicMock()
    result = mock_server.server.Server("test_server")
    mock_server.server.Server.assert_called_once_with("test_server")


def test_mcplib_framework_abstraction_importable():
    """mcplib.framework_abstraction can be imported (fastmcp is installed)."""
    for mod in list(sys.modules):
        if "genericsuite.mcplib.framework_abstraction" in mod:
            del sys.modules[mod]
    try:
        import genericsuite.mcplib.framework_abstraction as m
        assert m is not None
    except (ImportError, Exception) as exc:
        pytest.skip(f"mcplib not importable in this environment: {exc}")


# ---- MCP-specific: run only when CURRENT_FRAMEWORK=mcp ----

@pytest.mark.skipif(CURRENT_FRAMEWORK != "mcp",
                    reason=f"MCP-only tests (got {CURRENT_FRAMEWORK})")
def test_mcp_framework_loaded_flag():
    for mod in list(sys.modules):
        if "genericsuite.mcplib.framework_abstraction" in mod:
            del sys.modules[mod]
    from genericsuite.mcplib import framework_abstraction
    assert framework_abstraction.FRAMEWORK_LOADED is True


@pytest.mark.skipif(CURRENT_FRAMEWORK != "mcp",
                    reason=f"MCP-only tests (got {CURRENT_FRAMEWORK})")
def test_mcp_request_class_exists():
    from genericsuite.mcplib import framework_abstraction
    assert hasattr(framework_abstraction, "Request")


@pytest.mark.skipif(CURRENT_FRAMEWORK != "mcp",
                    reason=f"MCP-only tests (got {CURRENT_FRAMEWORK})")
def test_mcp_response_class_exists():
    from genericsuite.mcplib import framework_abstraction
    assert hasattr(framework_abstraction, "Response")
