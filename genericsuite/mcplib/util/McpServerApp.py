# MCP Server App class
from fastmcp import FastMCP

from genericsuite.config.config import Config
from genericsuite.config.config_from_db import set_init_custom_data
from genericsuite.util.utilities import get_non_empty_value


DEBUG = False

MCP_TRANSPORT = get_non_empty_value("MCP_TRANSPORT", "http")    # stdio or http
MCP_SERVER_HOST = get_non_empty_value("MCP_SERVER_HOST", "0.0.0.0")
try:
    MCP_SERVER_PORT = int(get_non_empty_value("MCP_SERVER_PORT", "8070"))
except ValueError:
    raise ValueError("MCP_SERVER_PORT must be an integer.")


class McpServerApp:
    """
    MCP Server App class
    """
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

    def run(self):
        mcp_run_args = {
            "transport": MCP_TRANSPORT
        }
        if MCP_TRANSPORT == "http":
            mcp_run_args["host"] = MCP_SERVER_HOST
            mcp_run_args["port"] = MCP_SERVER_PORT
        _ = DEBUG and print(f"Running MCP Server on {mcp_run_args}")
        self.mcp.run(**mcp_run_args)
