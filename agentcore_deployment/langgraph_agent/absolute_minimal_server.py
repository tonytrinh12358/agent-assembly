#!/usr/bin/env python3
"""
Absolute minimal MCP server - no parameters, simplest possible tool
"""

from mcp.server.fastmcp import FastMCP

# Create the simplest possible MCP server
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool()
def hello():
    """Absolute simplest tool - no parameters"""
    return {"message": "hello", "working": True}

if __name__ == "__main__":
    print("🔧 Starting absolute minimal MCP server...")
    mcp.run(transport="streamable-http", port=8000)
