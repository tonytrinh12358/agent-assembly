#!/usr/bin/env python3
"""
MCP server using direct tool registration instead of @mcp.tool() decorator
This might bypass any decorator-related issues
"""

import logging
import sys
import os
import traceback
from mcp.server.fastmcp import FastMCP

# Configure comprehensive stderr logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

def log_environment():
    """Log environment variables for debugging"""
    logger.info("=== DIRECT REGISTRATION MCP SERVER ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("=== END ENVIRONMENT DEBUG ===")

# Log environment on startup
log_environment()

# Create FastMCP server
logger.info("Creating FastMCP server with direct tool registration")
mcp = FastMCP(host="0.0.0.0", stateless_http=True)
logger.info("FastMCP server created successfully")

def direct_hello_tool():
    """Direct tool function - no decorator"""
    logger.info("========== DIRECT TOOL EXECUTION START ==========")
    logger.info("Direct hello tool called")
    
    try:
        logger.info("Creating direct response...")
        response_data = {
            "message": "direct_hello_working",
            "method": "direct_registration", 
            "success": True
        }
        
        logger.info(f"Direct response created: {response_data}")
        logger.info("========== DIRECT TOOL EXECUTION SUCCESS ==========")
        
        return response_data
        
    except Exception as e:
        logger.error("========== DIRECT TOOL EXECUTION ERROR ==========")
        logger.error(f"Direct tool exception: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("========== END DIRECT TOOL ERROR ==========")
        
        return {"error": f"Direct tool failed: {str(e)}", "success": False}

def direct_param_tool(test_input: str = "default_direct"):
    """Direct tool with parameters - no decorator"""
    logger.info("========== DIRECT PARAM TOOL START ==========")
    logger.info(f"Direct param tool called with: {test_input}")
    
    try:
        response = {
            "received": test_input,
            "method": "direct_registration_with_params",
            "success": True
        }
        
        logger.info(f"Direct param response: {response}")
        logger.info("========== DIRECT PARAM TOOL SUCCESS ==========")
        return response
        
    except Exception as e:
        logger.error(f"Direct param tool error: {e}")
        return {"error": str(e), "success": False}

# Register tools directly (not using @mcp.tool() decorator)
logger.info("Registering tools directly...")
try:
    # Try to register tools directly with FastMCP
    # This bypasses the @mcp.tool() decorator which might be causing issues
    logger.info("Attempting direct tool registration...")
    
    # NOTE: FastMCP might not support direct registration like this
    # If this fails, the @mcp.tool() decorator might be required
    # But let's try the decorator approach one more time with minimal code
    
    @mcp.tool()
    def minimal_test():
        """Absolute minimal tool using decorator"""
        logger.info("MINIMAL DECORATOR TOOL CALLED")
        return {"minimal": True, "status": "ok"}
    
    logger.info("Tool registration completed")
    
except Exception as e:
    logger.error(f"Tool registration failed: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    logger.info("=== STARTING DIRECT REGISTRATION MCP SERVER ===")
    
    try:
        logger.info("Starting mcp.run()...")
        mcp.run(transport="streamable-http", port=8000)
        
    except Exception as e:
        logger.error("=== DIRECT REGISTRATION SERVER ERROR ===")
        logger.error(f"Server startup failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
