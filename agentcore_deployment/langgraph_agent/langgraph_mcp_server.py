#!/usr/bin/env python3
"""
Comprehensive MCP server debugging version
Based on web search insights for MCP debugging
"""

import logging
import sys
import os
import traceback
from mcp.server.fastmcp import FastMCP

# Configure comprehensive stderr logging (critical for MCP debugging)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stderr  # Critical: use stderr to avoid corrupting MCP protocol
)

logger = logging.getLogger(__name__)

def log_environment():
    """Log environment variables for debugging"""
    logger.info("=== MCP SERVER ENVIRONMENT DEBUG ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Log key environment variables
    env_vars = ['HOME', 'PATH', 'USER', 'PWD', 'PYTHONPATH']
    for var in env_vars:
        value = os.environ.get(var, 'NOT_SET')
        logger.info(f"ENV {var}: {value[:100]}{'...' if len(str(value)) > 100 else ''}")
    
    logger.info("=== END ENVIRONMENT DEBUG ===")

# Log environment on startup
log_environment()

# Create FastMCP server with debugging
logger.info("Creating FastMCP server with stateless_http=True")
mcp = FastMCP(host="0.0.0.0", stateless_http=True)
logger.info("FastMCP server created successfully")

@mcp.tool()
def hello():
    """Ultra simple test tool with comprehensive debugging"""
    logger.info("========== TOOL EXECUTION START ==========")
    logger.info("Tool 'hello' called with no parameters")
    
    try:
        logger.info("Creating response data...")
        response_data = {"message": "hello", "working": True, "debug": "tool_executed"}
        
        logger.info(f"Response data created: {response_data}")
        logger.info("Tool 'hello' executing successfully")
        logger.info("========== TOOL EXECUTION SUCCESS ==========")
        
        return response_data
        
    except Exception as e:
        logger.error("========== TOOL EXECUTION ERROR ==========")
        logger.error(f"Exception in 'hello' tool: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("========== END TOOL EXECUTION ERROR ==========")
        
        # Return error in a format that won't break MCP
        return {"error": f"Tool execution failed: {str(e)}", "working": False}

@mcp.tool()  
def test_with_params(test_param: str = "default"):
    """Test tool with parameters"""
    logger.info("========== PARAMETRIZED TOOL START ==========")
    logger.info(f"Tool 'test_with_params' called with: test_param='{test_param}'")
    
    try:
        response = {
            "received_param": test_param,
            "param_type": type(test_param).__name__,
            "success": True
        }
        
        logger.info(f"Parametrized tool response: {response}")
        logger.info("========== PARAMETRIZED TOOL SUCCESS ==========")
        return response
        
    except Exception as e:
        logger.error(f"Parametrized tool error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e), "success": False}

if __name__ == "__main__":
    logger.info("=== STARTING MCP SERVER ===")
    logger.info("Server configuration:")
    logger.info("  Host: 0.0.0.0")
    logger.info("  Transport: streamable-http") 
    logger.info("  Port: 8000")
    logger.info("  Stateless HTTP: True")
    
    try:
        logger.info("Calling mcp.run()...")
        mcp.run(transport="streamable-http", port=8000)
        logger.info("mcp.run() completed")
        
    except Exception as e:
        logger.error("=== MCP SERVER STARTUP ERROR ===")
        logger.error(f"Failed to start MCP server: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("=== END STARTUP ERROR ===")
        sys.exit(1)
