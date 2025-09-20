# MCP Client App Class

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from genericsuite.config.config import Config
from genericsuite.util.app_logger import log_info, log_error


DEBUG = False


class McpClientApp:
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
