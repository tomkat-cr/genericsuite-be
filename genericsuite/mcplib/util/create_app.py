"""
App main module (create_app) for MCP
"""
import sys

from genericsuite.util.app_logger import log_info, log_error
from genericsuite.config.config import Config
from genericsuite.mcplib.util.McpServerApp import McpServerApp
from genericsuite.mcplib.util.McpClientApp import McpClientApp

DEBUG = False


def create_app(app_name: str = None, settings: Config = None) -> McpServerApp:
    """
    Create the MCP Server App
    """
    app = McpServerApp(app_name, settings)

    # Announce app boot
    _ = app.allow_log_info and log_info(
        f"{app.app_name.capitalize()} v" +
        app.settings.APP_VERSION +
        " | MCP server running")
    if DEBUG and app.allow_log_info:
        log_info(app.settings.debug_vars())

    return app


async def create_client_app():
    """
    Main test runner
    """
    app = McpClientApp()
    success = await app.connect_to_server()

    if not success:
        _ = app.allow_log_info and log_info(
            "❌ GS MCP Client - could not connect to server")
        sys.exit(1)

    _ = app.allow_log_info and log_error(
        "✅ GS MCP Client - connected to server")


# if __name__ == "__main__":
#     asyncio.run(create_client_app())
