"""
Base MCP Server Implementation for AWS Bedrock AgentCore Runtime
Provides common functionality for creating MCP servers.
"""

import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

class AgentCoreMCPServer:
    """Base class for AgentCore MCP servers"""
    
    def __init__(self, agent_name: str, description: str, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize MCP server
        
        Args:
            agent_name: Name of the agent
            description: Description of the agent
            host: Host to bind to
            port: Port to bind to
        """
        self.agent_name = agent_name
        self.description = description
        self.host = host
        self.port = port
        
        # Initialize FastMCP with stateless HTTP (required for AgentCore)
        self.mcp = FastMCP(host=self.host, stateless_http=True)
        
        logger.info(f"Initialized {agent_name} MCP server on {host}:{port}")
    
    def add_tool(self, func):
        """Add a tool to the MCP server"""
        return self.mcp.tool()(func)
    
    def run(self):
        """Start the MCP server"""
        logger.info(f"Starting {self.agent_name} MCP server...")
        self.mcp.run(transport="streamable-http", port=self.port)

def create_success_response(result: Any, tool_name: str = None, agent_name: str = None) -> Dict[str, Any]:
    """Create a standardized success response"""
    return {
        "result": result,
        "status": "success",
        "tool_name": tool_name,
        "agent_name": agent_name
    }

def create_error_response(error_message: str, tool_name: str = None, agent_name: str = None) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "error": error_message,
        "status": "failed",
        "tool_name": tool_name,
        "agent_name": agent_name
    }
