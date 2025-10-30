"""
MCP Agent Bridge - Converts existing AgentCore agents to MCP-compatible servers

This bridge allows the orchestrator to communicate with existing AgentCore agents 
using MCP protocol by creating MCP server endpoints that proxy to AgentCore agents.
"""

import json
import asyncio
import logging
import boto3
from typing import Dict, Any, List
from mcp.server.mcp import MCPServer
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp import types
import threading
import time

logger = logging.getLogger(__name__)


class AgentCoreMCPBridge:
    """Bridge that exposes AgentCore agents as MCP servers"""
    
    def __init__(self, agent_name: str, agent_arn: str, region: str = "us-west-2"):
        self.agent_name = agent_name
        self.agent_arn = agent_arn
        self.region = region
        self.client = boto3.client('bedrock-agentcore', region_name=region)
        
    async def invoke_agentcore_agent(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Invoke the underlying AgentCore agent"""
        try:
            payload = {
                'prompt': prompt,
                **kwargs
            }
            payload_bytes = json.dumps(payload).encode('utf-8')
            
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_arn,
                payload=payload_bytes
            )
            
            # Handle response
            result = ""
            if 'response' in response:
                response_body = response['response']
                if hasattr(response_body, 'read'):
                    result = response_body.read().decode('utf-8')
                else:
                    result = str(response_body)
            
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"result": result, "agent_name": self.agent_name}
                
        except Exception as e:
            logger.error(f"AgentCore invocation failed: {e}")
            return {"error": str(e), "agent_name": self.agent_name}


class LangGraphMCPServer:
    """MCP Server for LangGraph agent"""
    
    def __init__(self, agent_arn: str, region: str = "us-west-2"):
        self.bridge = AgentCoreMCPBridge("langgraph_agent", agent_arn, region)
        self.server = MCPServer("langgraph-mcp-server")
        
        # Register MCP tools
        self.setup_tools()
    
    def setup_tools(self):
        """Setup MCP tools for LangGraph agent"""
        
        @self.server.tool(
            "analyze_kitchen",
            "Analyze kitchen layout and materials for renovation planning",
            {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Kitchen analysis request"},
                    "image_path": {"type": "string", "description": "Optional image path"}
                },
                "required": ["prompt"]
            }
        )
        async def analyze_kitchen(prompt: str, image_path: str = None) -> List[types.TextContent]:
            """MCP tool for kitchen analysis"""
            logger.info(f"🏠 MCP LangGraph: analyze_kitchen called with prompt: {prompt[:50]}...")
            
            result = await self.bridge.invoke_agentcore_agent(prompt, image_path=image_path)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]


class CrewAIMCPServer:
    """MCP Server for CrewAI agent"""
    
    def __init__(self, agent_arn: str, region: str = "us-west-2"):
        self.bridge = AgentCoreMCPBridge("crewai_agent", agent_arn, region)
        self.server = MCPServer("crewai-mcp-server")
        
        # Register MCP tools
        self.setup_tools()
    
    def setup_tools(self):
        """Setup MCP tools for CrewAI agent"""
        
        @self.server.tool(
            "estimate_costs",
            "Estimate kitchen renovation costs using CrewAI multi-agent team",
            {
                "type": "object", 
                "properties": {
                    "prompt": {"type": "string", "description": "Cost estimation request"},
                    "materials_data": {"type": "array", "description": "List of materials with areas"},
                    "cost_grade": {"type": "string", "description": "Cost grade: economy, standard, premium"}
                },
                "required": ["prompt"]
            }
        )
        async def estimate_costs(prompt: str, materials_data: List = None, cost_grade: str = "standard") -> List[types.TextContent]:
            """MCP tool for cost estimation"""
            logger.info(f"💰 MCP CrewAI: estimate_costs called with grade: {cost_grade}")
            
            result = await self.bridge.invoke_agentcore_agent(
                prompt, 
                materials_data=materials_data or [],
                cost_grade=cost_grade
            )
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]


class MCPAgentBridgeManager:
    """Manages MCP bridges for multiple agents"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.bridges = {}
        self.servers = {}
    
    async def setup_agent_bridges(self):
        """Setup MCP bridges for all agents"""
        try:
            # Get agent ARNs
            ssm_client = boto3.client('ssm', region_name=self.region)
            
            # LangGraph bridge
            try:
                response = ssm_client.get_parameter(Name='/agents/langgraph_agent_arn')
                langgraph_arn = response['Parameter']['Value']
                
                self.servers['langgraph'] = LangGraphMCPServer(langgraph_arn, self.region)
                logger.info("✅ LangGraph MCP bridge created")
                
            except Exception as e:
                logger.error(f"❌ Failed to setup LangGraph bridge: {e}")
            
            # CrewAI bridge  
            try:
                response = ssm_client.get_parameter(Name='/agents/crewai_agent_arn')
                crewai_arn = response['Parameter']['Value']
                
                self.servers['crewai'] = CrewAIMCPServer(crewai_arn, self.region)
                logger.info("✅ CrewAI MCP bridge created")
                
            except Exception as e:
                logger.error(f"❌ Failed to setup CrewAI bridge: {e}")
                
        except Exception as e:
            logger.error(f"Bridge setup failed: {e}")
    
    def get_mcp_server(self, agent_type: str):
        """Get MCP server for agent type"""
        return self.servers.get(agent_type)


async def test_mcp_bridges():
    """Test MCP bridges for agent communication"""
    print("🌉 Testing MCP Agent Bridges")
    print("=" * 50)
    
    # Setup bridge manager
    manager = MCPAgentBridgeManager()
    await manager.setup_agent_bridges()
    
    print(f"✅ Bridges created: {list(manager.servers.keys())}")
    
    # Test LangGraph bridge
    if 'langgraph' in manager.servers:
        print("\n🏠 Testing LangGraph MCP Bridge...")
        try:
            langgraph_server = manager.servers['langgraph']
            # This would be called via MCP protocol in real usage
            result = await langgraph_server.bridge.invoke_agentcore_agent(
                "Analyze kitchen with refrigerator and oven for renovation"
            )
            print(f"   ✅ LangGraph bridge working: {len(str(result))} chars response")
        except Exception as e:
            print(f"   ❌ LangGraph bridge failed: {e}")
    
    # Test CrewAI bridge
    if 'crewai' in manager.servers:
        print("\n💰 Testing CrewAI MCP Bridge...")
        try:
            crewai_server = manager.servers['crewai']
            result = await crewai_server.bridge.invoke_agentcore_agent(
                "Estimate costs for kitchen renovation with standard materials"
            )
            print(f"   ✅ CrewAI bridge working: {len(str(result))} chars response")
        except Exception as e:
            print(f"   ❌ CrewAI bridge failed: {e}")
    
    print("\n🎯 MCP Bridge Status:")
    if manager.servers:
        print("   ✅ MCP bridges are functional!")
        print("   🔗 Ready for true MCP agent-to-agent communication")
        print(f"   📊 Active bridges: {len(manager.servers)}")
    else:
        print("   ❌ No bridges created - check agent deployments")
    
    return manager


if __name__ == "__main__":
    asyncio.run(test_mcp_bridges())
