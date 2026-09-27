"""Entry point for MCP server: python -m rubber_ducky.mcp"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
