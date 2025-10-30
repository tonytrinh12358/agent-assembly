#!/usr/bin/env python3
"""
Ultra-minimal MCP server test - bypasses all our custom code
"""

from mcp.server.fastmcp import FastMCP

# Create the simplest possible MCP server
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool()
def test_simple():
    """Ultra simple test tool"""
    return {"test": "success", "value": 42}

if __name__ == "__main__":
    print("🔧 Starting ultra-minimal MCP server...")
    mcp.run(transport="streamable-http", port=8000)
