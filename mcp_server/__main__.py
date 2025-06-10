"""
PyTaskAI MCP Server Entry Point

This module provides the entry point for running the PyTaskAI MCP server
with the command: python -m mcp_server
"""

import logging
import sys
from .task_manager import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting PyTaskAI MCP Server...")
        # Run the FastMCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
