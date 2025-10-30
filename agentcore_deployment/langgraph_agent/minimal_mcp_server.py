#!/usr/bin/env python3
"""
Ultra-minimal MCP server for LangGraph agent - debugging version
"""

from mcp.server.fastmcp import FastMCP

# Create the simplest possible MCP server
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool()
def analyze_kitchen(prompt: str = "test", image_data: str = None, image_path: str = None):
    """Ultra simple kitchen analysis - debugging"""
    return {
        "status": "success",
        "detected_objects": [{"name": "refrigerator", "confidence": 0.85}],
        "materials": [{"material_type": "granite", "area_sqm": 15.0}],
        "analysis": "Test kitchen analysis via minimal MCP server"
    }

if __name__ == "__main__":
    print("🔧 Starting ultra-minimal LangGraph MCP server...")
    mcp.run(transport="streamable-http", port=8000)
