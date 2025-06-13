"""
Main entry point for PyTaskAI MCP Server.

This module provides the entry point for running the MCP server using
`python -m mcp_server` as referenced in CLAUDE.md and MCP client configurations.
"""

import asyncio
import sys

from pytaskai.adapters.mcp.mcp_server import main

if __name__ == "__main__":
    # Run the MCP server main function
    asyncio.run(main())
