"""
Tests for genericsuite/mcplib/util/McpServerApp.py — McpServerApp class.

Tests run only when CURRENT_FRAMEWORK=mcp.  FastMCP is mocked so no
real MCP server is started.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

CURRENT_FRAMEWORK = os.environ.get("CURRENT_FRAMEWORK", "fastapi").lower()

pytestmark = pytest.mark.skipif(
    CURRENT_FRAMEWORK != "mcp",
    reason="MCP server app tests only run with CURRENT_FRAMEWORK=mcp",
)


def _setup_mcp_mocks():
    """Set up stubs so McpServerApp can be imported without a real FastMCP."""
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    sys.modules.setdefault("genericsuite.config.config_from_db", MagicMock())


def _import_mcp_server_app():
    _setup_mcp_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.mcplib.util.McpServerApp":
            del sys.modules[mod]
    from genericsuite.mcplib.util.McpServerApp import McpServerApp
    return McpServerApp


# ---- Module constants ----

def test_mcp_server_app_module_constants():
    _setup_mcp_mocks()
    import genericsuite.mcplib.util.McpServerApp as m
    assert hasattr(m, "MCP_TRANSPORT")
    assert hasattr(m, "MCP_SERVER_HOST")
    assert hasattr(m, "MCP_SERVER_PORT")
    assert isinstance(m.MCP_SERVER_PORT, int)


def test_mcp_transport_default():
    _setup_mcp_mocks()
    import genericsuite.mcplib.util.McpServerApp as m
    assert m.MCP_TRANSPORT in ("http", "stdio")


# ---- McpServerApp.__init__ ----

def test_mcp_server_app_init_with_mocked_fastmcp():
    McpServerApp = _import_mcp_server_app()
    mock_settings = MagicMock()
    mock_settings.APP_NAME = "test_app"

    with patch("genericsuite.mcplib.util.McpServerApp.FastMCP") as MockFastMCP, \
         patch("genericsuite.mcplib.util.McpServerApp.Config", return_value=mock_settings), \
         patch("genericsuite.mcplib.util.McpServerApp.set_init_custom_data",
               return_value={"key": "val"}):
        app = McpServerApp(app_name="my_app", settings=mock_settings)

    assert app.app_name == "my_app"
    assert app.settings is mock_settings
    MockFastMCP.assert_called_once_with("my_app")


def test_mcp_server_app_init_uses_settings_name_when_none():
    McpServerApp = _import_mcp_server_app()
    mock_settings = MagicMock()
    mock_settings.APP_NAME = "from_settings"

    with patch("genericsuite.mcplib.util.McpServerApp.FastMCP"), \
         patch("genericsuite.mcplib.util.McpServerApp.Config", return_value=mock_settings), \
         patch("genericsuite.mcplib.util.McpServerApp.set_init_custom_data",
               return_value={}):
        app = McpServerApp(settings=mock_settings)

    assert app.app_name == "from_settings"


def test_mcp_server_app_custom_data_set():
    McpServerApp = _import_mcp_server_app()
    mock_settings = MagicMock()
    mock_settings.APP_NAME = "test"

    with patch("genericsuite.mcplib.util.McpServerApp.FastMCP"), \
         patch("genericsuite.mcplib.util.McpServerApp.Config", return_value=mock_settings), \
         patch("genericsuite.mcplib.util.McpServerApp.set_init_custom_data",
               return_value={"custom": "data"}):
        app = McpServerApp(app_name="test", settings=mock_settings)

    assert app.custom_data == {"custom": "data"}


def test_mcp_server_app_run_http_mode():
    McpServerApp = _import_mcp_server_app()
    mock_settings = MagicMock()
    mock_settings.APP_NAME = "test"

    with patch("genericsuite.mcplib.util.McpServerApp.FastMCP") as MockFastMCP, \
         patch("genericsuite.mcplib.util.McpServerApp.Config", return_value=mock_settings), \
         patch("genericsuite.mcplib.util.McpServerApp.set_init_custom_data",
               return_value={}), \
         patch("genericsuite.mcplib.util.McpServerApp.MCP_TRANSPORT", "http"):
        app = McpServerApp(app_name="test", settings=mock_settings)
        app.run()

    # run() should call self.mcp.run(transport="http", host=..., port=...)
    MockFastMCP.return_value.run.assert_called_once()
    call_kwargs = MockFastMCP.return_value.run.call_args[1]
    assert call_kwargs.get("transport") == "http"


def test_mcp_server_app_run_stdio_mode():
    McpServerApp = _import_mcp_server_app()
    mock_settings = MagicMock()
    mock_settings.APP_NAME = "test"

    with patch("genericsuite.mcplib.util.McpServerApp.FastMCP") as MockFastMCP, \
         patch("genericsuite.mcplib.util.McpServerApp.Config", return_value=mock_settings), \
         patch("genericsuite.mcplib.util.McpServerApp.set_init_custom_data",
               return_value={}), \
         patch("genericsuite.mcplib.util.McpServerApp.MCP_TRANSPORT", "stdio"):
        app = McpServerApp(app_name="test", settings=mock_settings)
        app.run()

    call_kwargs = MockFastMCP.return_value.run.call_args[1]
    assert call_kwargs.get("transport") == "stdio"
    assert "host" not in call_kwargs
