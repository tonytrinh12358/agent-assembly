#!/usr/bin/env python3
"""
Local MCP server testing - Test MCP servers running locally before deployment
"""

import asyncio
import json
import logging
from datetime import timedelta
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_local_mcp_server(port: int = 8000, server_name: str = "MCP Server"):
    """Test a locally running MCP server"""
    mcp_url = f"http://localhost:{port}/mcp"
    headers = {}

    try:
        logger.info(f"🔌 Connecting to {server_name} at {mcp_url}")
        
        async with streamablehttp_client(
            mcp_url, 
            headers, 
            timeout=timedelta(seconds=30),
            terminate_on_close=False
        ) as (read_stream, write_stream, _):
            
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                logger.info("✅ MCP session initialized")
                
                # List tools
                tool_result = await session.list_tools()
                logger.info(f"📋 Available tools ({len(tool_result.tools)}):")
                
                for tool in tool_result.tools:
                    logger.info(f"  🔧 {tool.name}: {tool.description}")
                
                # Test basic tool if available
                if tool_result.tools:
                    test_tool = tool_result.tools[0]
                    logger.info(f"🧪 Testing tool: {test_tool.name}")
                    
                    try:
                        # Try to call the tool (this will depend on the specific tool)
                        if test_tool.name == "get_agent_info":
                            result = await session.call_tool(test_tool.name, {})
                            logger.info("✅ Tool test successful")
                            if hasattr(result, 'content') and result.content:
                                logger.info(f"📤 Result: {result.content[0].text[:100]}...")
                        else:
                            logger.info(f"ℹ️ Skipping test for tool: {test_tool.name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Tool test failed: {e}")
                
                logger.info(f"✅ {server_name} test completed successfully")
                return True
                
    except Exception as e:
        logger.error(f"❌ Failed to test {server_name}: {e}")
        return False


async def test_all_local_agents():
    """Test all MCP agents running locally"""
    logger.info("🚀 Testing all local MCP agents...")
    
    agents = [
        {"name": "LangGraph Agent", "port": 8000},
        {"name": "CrewAI Agent", "port": 8001},
        {"name": "Orchestrator Agent", "port": 8002}
    ]
    
    results = {}
    for agent in agents:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing {agent['name']}")
        logger.info(f"{'='*50}")
        
        success = await test_local_mcp_server(agent["port"], agent["name"])
        results[agent["name"]] = success
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("📊 TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    successful = sum(results.values())
    total = len(results)
    
    for agent_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{agent_name}: {status}")
    
    logger.info(f"\nOverall: {successful}/{total} agents passed")
    
    return results


if __name__ == "__main__":
    print("🧪 Local MCP Server Testing Suite")
    print("=" * 60)
    print("Make sure your MCP servers are running locally:")
    print("- LangGraph: python langgraph_agent/langgraph_mcp_server.py (port 8000)")
    print("- CrewAI: python crewai_agent/crewai_mcp_server.py (port 8001)")
    print("- Orchestrator: python orchestrator_agent/orchestrator_mcp_server.py (port 8002)")
    print("=" * 60)
    
    asyncio.run(test_all_local_agents())
