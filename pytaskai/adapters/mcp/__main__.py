"""
Module entry point for PyTaskAI MCP adapter.

This allows running the MCP server with:
python -m pytaskai.adapters.mcp
"""

import asyncio

from pytaskai.adapters.mcp.mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())
