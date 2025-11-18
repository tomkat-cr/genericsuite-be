"""
App main module (create_app) for MCP
"""
from typing import Any
import sys

from mcp.types import CallToolResult

from genericsuite.util.app_logger import log_info, log_error, set_app_logs
from genericsuite.config.config import Config
from genericsuite.mcplib.util.McpServerApp import McpServerApp
from genericsuite.mcplib.util.McpClientApp import McpClientApp

DEBUG = False


def create_app(app_name: str = None, settings: Config = None,
               log_file: str = None) -> McpServerApp:
    """
    Create the MCP Server App
    """
    if log_file:
        set_app_logs(log_file=log_file)

    app = McpServerApp(app_name, settings)

    # Announce app boot
    _ = app.allow_log_info and log_info(
        f"{app.app_name.capitalize()} v" +
        app.settings.APP_VERSION +
        " | MCP server running")
    if DEBUG and app.allow_log_info:
        log_info(app.settings.debug_vars())

    return app


async def run_client_app(tool_name: str, arguments: dict[str, Any] | None
                         ) -> CallToolResult:
    """
    Main test runner using the async context manager pattern.

    Usage example:
        async with McpClientApp(allow_log_info=True) as client:
            # Use client.session to interact with the MCP server
            result = await client.session.call_tool(...)
    """
    try:
        async with McpClientApp(allow_log_info=True) as app:
            _ = app.allow_log_info and log_info(
                "✅ GS MCP Client - connected to server")

            result = await app.session.call_tool(tool_name, arguments)
            return result

    except Exception as e:
        log_error(f"❌ GS MCP Client - could not connect to server: {e}")
        sys.exit(1)


# if __name__ == "__main__":
#     asyncio.run(run_client_app(tool_name="test", arguments=None))
