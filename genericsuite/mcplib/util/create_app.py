"""
App main module (create_app) for MCP
"""
# For MCP Client
import sys
# import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# For MCP Server
from fastmcp import FastMCP

# from genericsuite.mcplib.framework_abstraction import (
#     Request,
#     Blueprint,
# )

from genericsuite.util.app_logger import log_info, log_error
from genericsuite.config.config import Config
from genericsuite.config.config_from_db import set_init_custom_data

DEBUG = False


# ----------------------- MCP Server App Class -----------------------


class MCPServerApp:
    """
    MCP Server App class
    """
    # request: Request = None
    # blueprint: Blueprint = None
    # other_params: dict = {}

    app_name: str = None
    settings: Config = None
    mcp: FastMCP = None
    custom_data: dict = {}
    allow_log_info: bool = False

    def __init__(self, app_name: str = None, settings: Config = None,
                 allow_log_info: bool = False):
        """
        Initialize the MCP Server App Class
        """
        if settings is None:
            settings = Config()

        if app_name is None:
            app_name = settings.APP_NAME

        self.app_name = app_name
        self.settings = settings
        self.allow_log_info = allow_log_info

        # Initialize FastMCP server
        self.mcp = FastMCP(app_name)

        # Custom data, to be used to store a dict for
        # GenericDbHelper specific functions
        self.custom_data = set_init_custom_data()


def create_app(app_name: str = None, settings: Config = None) -> MCPServerApp:
    """
    Create the MCP Server App
    """
    app = MCPServerApp(app_name, settings)

    # Announce app boot
    _ = app.allow_log_info and log_info(
        f"{app.app_name.capitalize()} v" +
        app.settings.APP_VERSION +
        " | MCP server running")
    if DEBUG and app.allow_log_info:
        log_info(app.settings.debug_vars())

    return app

# ----------------------- MCP Client App Class -----------------------


class MCPClientApp:
    """
    MCP Client App class
    """
    allow_log_info: bool = False

    def __init__(self, app_name: str = None, settings: Config = None,
                 server_script_path: str = None,
                 allow_log_info: bool = False):
        """
        Initialize the MCP Client App Class
        """
        if settings is None:
            settings = Config()

        if app_name is None:
            app_name = settings.APP_NAME

        self.app_name = app_name
        self.settings = settings

        self.allow_log_info = allow_log_info

        self.session = None

        self.server_script_path = server_script_path
        if self.server_script_path is None:
            self.server_script_path = "genericsuite.mcplib.endpoints.users.py"

    async def connect_to_server(self):
        """
        Connect to the running MCP server
        """
        _ = self.allow_log_info and log_info(
            f"🔌 Connecting to {self.app_name} MCP Server...")

        try:
            # Connect to server via STDIO
            server_params = StdioServerParameters(
                command="python",
                args=[self.server_script_path],
                env=None
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    _ = self.allow_log_info and log_info(
                        "✅ Connected to MCP server successfully!")

                    # Initialize the session
                    await session.initialize()
                    _ = self.allow_log_info and log_info(
                        "✅ Session initialized!")

        except Exception as e:
            _ = self.allow_log_info and log_error(
                f"❌ Connection failed: {e}")
            return False

        return True


async def create_client_app():
    """
    Main test runner
    """
    app = MCPClientApp()
    success = await app.connect_to_server()

    if not success:
        _ = app.allow_log_info and log_info(
            "❌ GS MCP Client - could not connect to server")
        sys.exit(1)

    _ = app.allow_log_info and log_error(
        "✅ GS MCP Client - connected to server")


# if __name__ == "__main__":
#     asyncio.run(create_client_app())
