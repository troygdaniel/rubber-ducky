"""MCP server for rubber-ducky.

Exposes voice I/O tools for Claude Code integration.
"""

from .server import create_server

__all__ = ["create_server"]
