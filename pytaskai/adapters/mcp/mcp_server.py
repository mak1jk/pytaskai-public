"""
FastMCP server setup for PyTaskAI MCP adapter.

This module provides the main MCP server implementation using FastMCP,
following the Facade pattern to provide a simplified interface for
MCP clients to interact with PyTaskAI functionality.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

from fastmcp import FastMCP

from pytaskai.adapters.mcp.dependency_injection import (
    MCPContainer,
    create_mcp_container,
)
from pytaskai.adapters.mcp.task_tools import register_task_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        (
            logging.FileHandler("mcp_server.log")
            if os.path.exists(".")
            else logging.NullHandler()
        ),
    ],
)

logger = logging.getLogger(__name__)


class PyTaskAIMCPServer:
    """
    PyTaskAI MCP Server implementation.

    This server exposes PyTaskAI functionality through the MCP protocol,
    following the Facade pattern to provide a clean, simplified interface
    for MCP clients while hiding the complexity of the underlying
    hexagonal architecture.
    """

    def __init__(
        self,
        database_path: Optional[str] = None,
        debug: bool = False,
    ) -> None:
        """
        Initialize PyTaskAI MCP Server.

        Args:
            database_path: Optional database path override
            debug: Enable debug logging
        """
        self._debug = debug
        self._container: Optional[MCPContainer] = None
        self._mcp_app: Optional[FastMCP] = None
        self._database_path = database_path

        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")

    async def initialize(self) -> None:
        """
        Initialize the MCP server and all dependencies.

        This method sets up the dependency injection container,
        initializes the database, and registers all MCP tools.
        """
        try:
            logger.info("Initializing PyTaskAI MCP Server...")

            # Create dependency injection container
            self._container = create_mcp_container(database_path=self._database_path)

            # Verify container is ready
            if not self._container.is_ready():
                raise RuntimeError("Failed to initialize database connection")

            # Create FastMCP application
            self._mcp_app = FastMCP("pytaskai")

            # Register task management tools
            self._task_tools = register_task_tools(self._container, self._mcp_app)

            # Log service status
            status = self._container.get_service_status()
            logger.info(f"Service status: {status}")

            logger.info("PyTaskAI MCP Server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}", exc_info=True)
            raise

    async def run(self) -> None:
        """
        Run the MCP server.

        This method starts the FastMCP server and handles the MCP protocol
        communication with clients.
        """
        if not self._mcp_app:
            raise RuntimeError("MCP server not initialized. Call initialize() first.")

        try:
            logger.info("Starting PyTaskAI MCP Server...")

            # Run the FastMCP server
            await self._mcp_app.run()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"MCP server error: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the MCP server.

        This method closes database connections and cleans up resources.
        """
        logger.info("Shutting down PyTaskAI MCP Server...")

        try:
            if self._container:
                self._container.close_database()
                logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        logger.info("PyTaskAI MCP Server shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if the server is initialized."""
        return self._container is not None and self._mcp_app is not None

    @property
    def service_status(self) -> dict:
        """Get current service status."""
        if not self._container:
            return {"initialized": False}

        status = self._container.get_service_status()
        status["initialized"] = True
        return status


async def create_server(
    database_path: Optional[str] = None,
    debug: bool = False,
) -> PyTaskAIMCPServer:
    """
    Factory function to create and initialize PyTaskAI MCP Server.

    Args:
        database_path: Optional database path override
        debug: Enable debug logging

    Returns:
        Initialized PyTaskAIMCPServer instance
    """
    server = PyTaskAIMCPServer(database_path=database_path, debug=debug)
    await server.initialize()
    return server


async def main() -> None:
    """
    Main entry point for the MCP server.

    This function handles command line arguments, creates the server,
    and runs it until shutdown.
    """
    # Parse basic command line arguments
    debug = "--debug" in sys.argv or "-v" in sys.argv
    database_path = None

    # Look for --database-path argument
    for i, arg in enumerate(sys.argv):
        if arg == "--database-path" and i + 1 < len(sys.argv):
            database_path = sys.argv[i + 1]
            break

    # Create and run server
    try:
        server = await create_server(database_path=database_path, debug=debug)
        await server.run()

    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())
