# MCP Client App Class

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Optional

from genericsuite.config.config import Config
from genericsuite.util.app_logger import log_info, log_error


DEBUG = False


class McpClientApp:
    """
    MCP Client App class - Async Context Manager for MCP Client
    connections.

    Usage:
        async with McpClientApp(
            app_name="MyApp", allow_log_info=True
        ) as client:
            # Use client.session here
            result = await client.session.call_tool(...)
        # Session is automatically closed here
    """
    allow_log_info: bool = False

    def __init__(self, app_name: str = None, settings: Config = None,
                 server_script_path: str = None,
                 allow_log_info: bool = False):
        """
        Initialize the MCP Client App Class

        Args:
            app_name: Name of the application
            settings: Configuration settings
            server_script_path: Path to the MCP server script
            allow_log_info: Enable logging
        """
        if settings is None:
            settings = Config()

        if app_name is None:
            app_name = settings.APP_NAME

        self.app_name = app_name
        self.settings = settings

        self.allow_log_info = allow_log_info

        self.session: Optional[ClientSession] = None

        # Context manager references to keep resources alive
        self._stdio_context = None
        self._session_context = None
        self._read = None
        self._write = None

        self.server_script_path = server_script_path
        if self.server_script_path is None:
            self.server_script_path = \
                "genericsuite.mcplib.endpoints.users.py"

    async def __aenter__(self):
        """
        Async context manager entry point.
        Establishes connection to MCP server and initializes session.

        Returns:
            self: The McpClientApp instance with an active session
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

            # Create and enter the stdio context
            self._stdio_context = stdio_client(server_params)
            self._read, self._write = \
                await self._stdio_context.__aenter__()

            _ = self.allow_log_info and log_info(
                "✅ Connected to MCP server successfully!")

            # Create and enter the session context
            self._session_context = ClientSession(self._read, self._write)
            self.session = await self._session_context.__aenter__()

            # Initialize the session
            await self.session.initialize()
            _ = self.allow_log_info and log_info(
                "✅ Session initialized!")

        except Exception as e:
            _ = self.allow_log_info and log_error(
                f"❌ Connection failed: {e}")
            # Clean up any partially initialized resources
            await self._cleanup()
            raise

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.
        Properly cleans up session and connection resources.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred

        Returns:
            False to propagate any exception that occurred
        """
        _ = self.allow_log_info and log_info(
            f"🔌 Disconnecting from {self.app_name} MCP Server...")

        await self._cleanup()

        _ = self.allow_log_info and log_info(
            "✅ Disconnected successfully!")

        return False  # Don't suppress exceptions

    async def _cleanup(self):
        """
        Internal cleanup method to close session and stdio contexts.
        Safe to call multiple times.
        """
        # Close session context if it exists
        if self._session_context is not None:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                _ = self.allow_log_info and log_error(
                    f"⚠️ Error closing session: {e}")
            finally:
                self._session_context = None
                self.session = None

        # Close stdio context if it exists
        if self._stdio_context is not None:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                _ = self.allow_log_info and log_error(
                    f"⚠️ Error closing stdio connection: {e}")
            finally:
                self._stdio_context = None
                self._read = None
                self._write = None
