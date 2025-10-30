#!/usr/bin/env python3
"""
Test MCP-based agent communication
"""

import asyncio
import sys
import os
from mcp_client_utils import test_mcp_agent_communication, MCPAgentClient


async def comprehensive_mcp_test():
    """Run comprehensive MCP testing"""
    print("🧪 Comprehensive MCP Agent Testing")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    print("\n📡 Test 1: MCP Agent Connectivity")
    print("-" * 40)
    await test_mcp_agent_communication()
    
    # Test 2: Tool discovery
    print("\n🔍 Test 2: Tool Discovery")
    print("-" * 40)
    client = MCPAgentClient()
    
    agents = ["langgraph_agent", "crewai_agent"]
    for agent in agents:
        try:
            print(f"\n🔧 {agent} tools:")
            tools = await client.list_agent_tools(agent)
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool['name']}: {tool['description']}")
            
            if not tools:
                print("   ⚠️  No tools found - agent may not be MCP-enabled")
        except Exception as e:
            print(f"   ❌ Failed to discover tools: {e}")
    
    # Test 3: Sample invocations
    print("\n🚀 Test 3: Sample MCP Invocations")
    print("-" * 40)
    
    try:
        print("\n🏠 Testing LangGraph via MCP...")
        from mcp_client_utils import invoke_langgraph_agent_mcp
        langgraph_result = await invoke_langgraph_agent_mcp("Test kitchen analysis")
        
        if "error" not in langgraph_result:
            print("   ✅ LangGraph MCP invocation successful")
            print(f"   📊 Response type: {type(langgraph_result)}")
            if isinstance(langgraph_result, dict):
                print(f"   📋 Keys: {list(langgraph_result.keys())}")
        else:
            print(f"   ❌ LangGraph MCP failed: {langgraph_result['error']}")
            
    except Exception as e:
        print(f"   ❌ LangGraph MCP test failed: {e}")
    
    try:
        print("\n💰 Testing CrewAI via MCP...")
        from mcp_client_utils import invoke_crewai_agent_mcp
        test_materials = [
            {"material_type": "wood", "area_sqm": 10},
            {"material_type": "granite", "area_sqm": 5}
        ]
        crewai_result = await invoke_crewai_agent_mcp(test_materials, "standard")
        
        if "error" not in crewai_result:
            print("   ✅ CrewAI MCP invocation successful")
            print(f"   📊 Response type: {type(crewai_result)}")
            if isinstance(crewai_result, dict):
                print(f"   📋 Keys: {list(crewai_result.keys())}")
        else:
            print(f"   ❌ CrewAI MCP failed: {crewai_result['error']}")
            
    except Exception as e:
        print(f"   ❌ CrewAI MCP test failed: {e}")
    
    print("\n🎯 Test Summary")
    print("-" * 40)
    print("If tests pass, your MCP setup is ready!")
    print("If tests fail, check:")
    print("1. Agent deployment status")
    print("2. MCP protocol support in agents")  
    print("3. Authentication and permissions")
    print("4. Network connectivity")


def test_mcp_requirements():
    """Test if MCP requirements are installed"""
    print("🔍 Checking MCP Requirements...")
    
    try:
        import mcp
        from mcp import ClientSession  
        from mcp.client.streamable_http import streamablehttp_client
        print("✅ MCP SDK: Installed")
    except ImportError as e:
        print(f"❌ MCP SDK: Missing - {e}")
        print("   Install with: pip install mcp>=1.17.1")
        return False
    
    try:
        import asyncio
        print("✅ AsyncIO: Available")
    except ImportError:
        print("❌ AsyncIO: Missing")
        return False
    
    try:
        import boto3
        print("✅ Boto3: Available")
    except ImportError:
        print("❌ Boto3: Missing")
        return False
        
    return True


async def main():
    """Main test function"""
    print("🎯 MCP Agent Testing Suite")
    print("=" * 60)
    
    # Check requirements first
    if not test_mcp_requirements():
        print("\n❌ Requirements check failed. Please install missing dependencies.")
        sys.exit(1)
    
    print("\n✅ Requirements check passed!")
    
    # Run comprehensive tests
    await comprehensive_mcp_test()
    
    print("\n🏁 MCP Testing Complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)
